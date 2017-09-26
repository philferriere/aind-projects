import math
import statistics
import warnings

import numpy as np
from hmmlearn.hmm import GaussianHMM
from sklearn.model_selection import KFold
from asl_utils import combine_sequences


class ModelSelector(object):
    '''
    base class for model selection (strategy design pattern)
    '''

    def __init__(self, all_word_sequences: dict, all_word_Xlengths: dict, this_word: str,
                 n_constant=3,
                 min_n_components=2, max_n_components=10,
                 random_state=14, verbose=False):
        self.words = all_word_sequences
        self.hwords = all_word_Xlengths
        self.sequences = all_word_sequences[this_word]
        self.X, self.lengths = all_word_Xlengths[this_word]
        self.this_word = this_word
        self.n_constant = n_constant
        self.min_n_components = min_n_components
        self.max_n_components = max_n_components
        self.random_state = random_state
        self.verbose = verbose

    def select(self):
        raise NotImplementedError

    def base_model(self, num_states):
        # with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        # warnings.filterwarnings("ignore", category=RuntimeWarning)
        try:
            hmm_model = GaussianHMM(n_components=num_states, covariance_type="diag", n_iter=1000,
                                    random_state=self.random_state, verbose=False).fit(self.X, self.lengths)
            if self.verbose:
                print("model created for {} with {} states".format(self.this_word, num_states))
            return hmm_model
        except:
            if self.verbose:
                print("failure on {} with {} states".format(self.this_word, num_states))
            return None


class SelectorConstant(ModelSelector):
    """ select the model with value self.n_constant

    """

    def select(self):
        """ select based on n_constant value

        :return: GaussianHMM object
        """
        best_num_components = self.n_constant
        return self.base_model(best_num_components)


class SelectorBIC(ModelSelector):
    """ select the model with the lowest Baysian Information Criterion(BIC) score

    http://www2.imm.dtu.dk/courses/02433/doc/ch6_slides.pdf
    Bayesian information criteria: BIC = -2 * logL + p * logN
    where:
      L is the likelihood of the fitted model,
      p is the number of parameters,
      N is the number of data points.
    The lower BIC the better.
    """

    def select(self):
        """ select the best model for self.this_word based on
        BIC score for n between self.min_n_components and self.max_n_components

        :return: GaussianHMM object
        """
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # Go through each model and compute its BIC score, only keeping track of the one with min BIC
        # If two BICs are mins, return the model with lower complexity
        best_num_components, lowest_BIC = None, None
        for num_components in range(self.min_n_components, self.max_n_components + 1):
            try:
                logL = self.base_model(num_components).score(self.X, self.lengths)
                logN = np.log(len(self.X))
                # Per https://discussions.udacity.com/t/number-of-parameters-bic-calculation/233235/3:
                # The parameters are the transition probabilities and the emission probabilities.
                # For the transition matrix, it's going to be a N x N matrix, where N is the number of states. The free parameters for the transition matrix is N * (N - 1). This is because the rows must sum up to one, so the last value is fixed to whatever value to add up to 1.
                # For the emission matrix, since the covariance_type is "diag" by default", if the model has M features, then there are M means and M diagonal values in the covariance matrix, for 2 * M per state. The final total is 2 * theNumberOfStates * theNumberOfFeatures.
                p = num_components * (num_components-1) + 2 * len(self.X[0]) * num_components
                BIC = -2 * logL + p * logN
                if lowest_BIC is None or lowest_BIC > BIC:
                    lowest_BIC, best_num_components = BIC, num_components
            except:
                pass

        if best_num_components is None:
            return self.base_model(self.n_constant)
        else:
            return self.base_model(best_num_components)

class SelectorDIC(ModelSelector):
    ''' select best model based on Discriminative Information Criterion

    Biem, Alain. "A model selection criterion for classification: Application to hmm topology optimization."
    Document Analysis and Recognition, 2003. Proceedings. Seventh International Conference on. IEEE, 2003.
    http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.58.6208&rep=rep1&type=pdf
    DIC = log(P(X(i)) - 1/(M-1)SUM(log(P(X(all but i))
    where:
      M is the number of words
      log(P(X(i)) is the log-likelihood of the fitted model for the current word,
      1/(M-1)SUM(log(P(X(all but i)) is the average of the log-likelihoods of the fitted models for all the other words,
    The higher DIC the better.
    '''

    def select(self):
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # Go through each model and compute its DIC score, only keeping track of the one with max DIC
        # If two DICs are maxs, return the model with lower complexity
        best_num_components, highest_DIC = None, None
        for num_components in range(self.min_n_components, self.max_n_components + 1):
            try:
                log_P_X_i = self.base_model(num_components).score(self.X, self.lengths)

                sum_log_P_X_all_but_i = 0.
                words = list(self.words.keys())
                M = len(words)
                words.remove(self.this_word)

                for word in words:
                    try:
                        model_selector_all_but_i = ModelSelector(self.words, self.hwords, word, self.n_constant, self.min_n_components, self.max_n_components, self.random_state, self.verbose)
                        sum_log_P_X_all_but_i += model_selector_all_but_i.base_model(num_components).score(model_selector_all_but_i.X, model_selector_all_but_i.lengths)
                    except:
                        M = M - 1

                DIC = log_P_X_i - sum_log_P_X_all_but_i / (M - 1)

                if highest_DIC is None or highest_DIC < DIC:
                  highest_DIC, best_num_components = DIC, num_components
            except:
                pass

        if best_num_components is None:
            return self.base_model(self.n_constant)
        else:
            return self.base_model(best_num_components)

class SelectorCV(ModelSelector):
    ''' select best model based on average log Likelihood of cross-validation folds
        The higher average log Likelihood the better.
        Note: here we explicitly use 3-fold CV
    '''
    NUM_FOLDS = 3

    def select(self):
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # Go through each model and compute its 3-fold average log Likelihood, only keeping track of the max value
        # If two 3-fold average log Likelihoods are maxs, return the model with lower complexity
        best_num_components, highest_avg_logL = None, None
        for num_components in range(self.min_n_components, self.max_n_components + 1):
            sum_logL = 0.
            count_logL = 0
            try:
                # Compute average log Likelihood, using jupyter notebook code as reference:
                # In order to run hmmlearn training using the X,lengths tuples on the new folds,
                # subsets must be combined based on the indices given for the folds.
                # A helper utility has been provided in the asl_utils module named combine_sequences for this purpose.
                split_method = KFold(SelectorCV.NUM_FOLDS)
                for cv_train_idx, cv_test_idx in split_method.split(self.sequences):
                    X, lengths = combine_sequences(cv_train_idx,self.sequences)

                    try:
                        sum_logL += self.base_model(num_components).score(X, lengths)
                        count_logL += 1
                    except:
                        pass

                if count_logL > 0:
                    avg_logL = sum_logL / count_logL
                    if highest_avg_logL is None or highest_avg_logL < avg_logL:
                      highest_avg_logL, best_num_components = avg_logL, num_components
            except:
                pass

        if best_num_components is None:
            return self.base_model(self.n_constant)
        else:
            return self.base_model(best_num_components)

