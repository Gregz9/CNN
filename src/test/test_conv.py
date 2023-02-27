from src.Layers import *
from src.FFNN import FFNN
import numpy as np
import imageio.v3 as imageio
import matplotlib.pyplot as plt

np.random.seed(2023)

""" 
Test file for Conv-layers and Pooling-layers 
"""


def init_test():
    layer = Convolution2DLayer(3, 3, 2, 2, "same", lambda x: x, 2023)

    assert layer.kernel_tensor is not None


def forward_test(image):
    layer = Convolution2DLayer(
        input_channels=3,
        feature_maps=64,
        kernel_size=2,
        stride=2,
        pad="same",
        act_func=lambda x: x,
        seed=2023,
    )

    conv_rest = layer._feedforward(image)

    assert conv_rest.shape == (128, 128, 64, 3)

    plt.imshow(conv_rest[:, :, 0, 0], vmin=0, vmax=255)
    plt.show()


def backward_test(X):
    layer = Convolution2DLayer(
        input_channels=3,
        feature_maps=64,
        kernel_size=2,
        stride=2,
        pad="same",
        act_func=lambda x: x,
        seed=2023,
    )

    # Shape of output we're testing with is (128, 128, 64, 3) -> (height, width, feature_maps, num_images)
    rand_grad = np.random.randn(128, 128, 64, 3)

    layer._backpropagate(X, rand_grad)


def max_pooling_test(X):
    pooling_layer = Pooling2DLayer(
        kernel_size=2,
        stride=2,
        pooling="max",
    )

    mpl_img = pooling_layer._feedforward(X)
    plt.imshow(mpl_img[0, 2, :, :], vmin=0, vmax=255, aspect="auto")
    plt.show()


if __name__ == "__main__":
    img_path = "/home/gregz/Files/CNN/data/luna.JPG"
    print(img_path)
    image = imageio.imread(img_path)
    images = np.ndarray((image.shape[0], image.shape[1], image.shape[2], 3))
    for i in range(3):
        images[:, :, :, i] = image[:, :, :]

    images = images.transpose(3, 2, 0, 1)

    # init_test()
    # forward_test(images)

    # backward_test(images)
    max_pooling_test(images)
