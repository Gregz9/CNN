# CNN
Readable CNN deep learning model codebase developed for the Center of Computing in Science Education at the University of Oslo, as well as a part of the project in subject FYS5429 - Advanced topics in machine learning and data analysis for physical sciences. 

The code developed here is based on a feed forward nueral network developed earlier in the subject FYS-STK3155/4155, for which the code and report can be found here: 
https://github.com/EricEReber/FFNN_optimization

While developing the convolutional nueral network, we decided to change the coding style and teh structure of our code to mimic machine learning frameworks Tensorflow and Pytorch, allowing for an intuitive and easy to understand approach to building neural networks. We divided our code into functional components called *Layers*, which as the name suggests are representations of the layers 
found in nerual networks. All the code used to build our models can be found in the directory ```src/```, while test files used for generating the results presented in ```doc/paper.pdf```can be found at ```src/test/```and are called ```mnist28.py``` and ```cifar10.py```. These scritps can be simply run using the following command: 

```
python3 <filename>.py
```

Information on how to contract and use the network, and descriptions of theory behind the mechanisms governing the network can be found in the jupyter-notebook file ```doc/CNN_in_Python.ipynb```. while the thoery part itself can be found in the *paper.pdf* in the same directory. 
