from src.Layers import *
from sklearn.datasets import load_breast_cancer
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from collections import OrderedDict
from src.FFNN import FFNN
from src.CNN import CNN
from src.costFunctions import CostOLS
import autograd.numpy as np
from src.Layers import FlattenLayer
import matplotlib.pyplot as plt
import imageio.v3 as imageio

"""
Test file to test replacing progress bar with ProgressBar class
"""

# simple dataset
cancer_dataset = load_breast_cancer()
cancer_X = cancer_dataset.data
cancer_t = cancer_dataset.target
cancer_t = cancer_t.reshape(cancer_t.shape[0], 1)

np.random.seed(1337)
X_train, X_val, t_train, t_val = train_test_split(cancer_X, cancer_t)
scaler = MinMaxScaler()
scaler.fit(X_train)
X_train = scaler.transform(X_train)
X_val = scaler.transform(X_val)


seed = 1337
rho = 0.9
rho2 = 0.999
momentum = 0.9
eta = 1e-3
lam = 1e-5
epochs = 200
batches = 10

adam_scheduler = Adam(eta, rho, rho2)
cnn = CNN(scheduler=adam_scheduler, seed=seed)

cnn.add_FullyConnectedLayer(X_train.shape[1], LRELU, seed=seed)

cnn.add_FullyConnectedLayer(100, LRELU, seed=seed)

cnn.add_OutputLayer(1, sigmoid, seed=seed)

cnn.fit_TEST_PROGBAR(
    X_train,
    t_train,
    lam=lam,
    batches=batches,
    epochs=epochs,
    X_val=X_val,
    t_val=t_val,
)