Artificial Intelligence Nanodegree Projects
===========================================

This repo contains our work on Udacity's [Artificial Intelligence Nanodegree](https://www.udacity.com/course/artificial-intelligence-nanodegree--nd889) Projects.

# Facial Keypoint Detection + Real-time Filtering [Capstone Project]
This exciting and fun capstone project required **combining traditional computer vision techniques and deep learning** to build and end-to-end facial keypoint recognition system. Fisrt, we used OpenCV to build a **face detector** and pre-process video input data. Second, we **trained a CNN to detect facial keypoints** in the face area of the video frame. Third, we used OpenCV again to apply a template (sunglasses) on top of the facial keypoints in real-time.

[![facial-keypoints1](img/cv-facialkeypoints1.png)](./cv-facialkeypoints/CV_project.ipynb)
[![facial-keypoints2](img/cv-facialkeypoints2.png)](./cv-facialkeypoints/CV_project.ipynb)

Our capstone project can be reviewed [here](./cv-facialkeypoints/CV_project.ipynb).

# CNN-based Dog Breed Classifier
For this computer vision problem, we experimented with two different **CNN (Convolutional Neural Network) architectures**. In our first approach, we built a CNN **from scratch**. Second, we used **transfer learning** to leverage pre-trained models (VGG-16, VGG-19, ResNet-50, Inception, Xception), only training the head of the network (the fully connected classification layer) for our specific application (84.8% test accuracy w. ResNet-50)

[![dog-project](img/dog-project.png)](./dog-project/dog_app.ipynb)

The notebook for this project can be found [here](./dog-project/dog_app.ipynb).

# Facial Expressions Identification

In this project, we use [Affectiva’s Emotion-as-a-Service API](https://developer.affectiva.com) to **track faces** in a video and **identify facial expressions**. We tag each face with an appropriate emoji next to it. If you own a webcam, you may also play a simple game: mimic a random emoji we display and we will automatically recognize if your expression matches our random selection!

[![cv-mimic](img/cv-mimic.png)](./cv-mimic/README.md)

Our implementation is available [here](./cv-mimic/README.md).

# Sign Language Recognition

Here, we use **HMMs (Hidden Markov Models)** to recognize gestures in American Sign Language, from individual words to complete sentences. We train our system on a dataset of videos that have been pre-processed and annotated, and test on novel sequences.

[![recognizer](img/demosample.png)](https://drive.google.com/open?id=0B_5qGuFe-wbhUXRuVnNZVnMtam8)

Click [here](./recognizer/asl_recognizer.ipynb) to review the IPython notebook for this project.

# Planning Search

For this project, we implement a planning search agent to solve deterministic logistics planning problems for an Air Cargo transport system. We use a **planning graph** and **automatic domain-independent heuristics with A* search** and compare their results/performance against several **uninformed non-heuristic search methods** (breadth-first, depth-first, etc.).

Additional details can be found [here](./planning/README.md).

# Game-Playing Agent

This game-playing agent uses techniques such as **iterative deepening**, **Minimax**, and **Alpha-Beta Pruning** to beat its opponent in a game of *Isolation* (a two-ply discrete competitive game with perfect information).

[![isolation](./img/isolation.png)](./isolation/README.md)

For details about our implementation, please visit this [link](./isolation/README.md).

# Diagonal Sudoku Solver

In this introductory project, we use **constraint propagation** to find solutions to Sudoku puzzles, repeatedly applying game rules (constraints) until the Sudoku puzzle stops changing.

[![cv-sudoku](./img/sudoku-anim.gif)](./cv-mimic/README.md)

For more information about this project, go [here](./sudoku/README.md).

# Contact Info

If you have any questions about this work, please feel free to contact us here:

[![https://www.linkedin.com/in/philferriere](img/LinkedInDLDev.png)](https://www.linkedin.com/in/philferriere)

