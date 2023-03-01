import math
import autograd.numpy as np
from copy import deepcopy, copy
from autograd import grad
from typing import Callable
from src.activationFunctions import *
from src.Schedulers import *

"""
Interface contatining all the layers that will be available for construction of 
a models architecture.
"""
# TODO: Start implementation of FullyConnected, Output and Convolution Layer


class Layer:
    def __init__(self, seed):
        self.seed = seed

    def _feedforward(self):
        raise NotImplementedError

    def _backpropagate(self):
        raise NotImplementedError

    def _reset_weights(self, prev_nodes):
        raise NotImplementedError


class FullyConnectedLayer(Layer):
    def __init__(
        self,
        nodes,
        act_func: Callable,
        scheduler: Scheduler,
        seed=None,
        is_first_layer=False,
    ):
        super().__init__(seed)
        self.nodes = nodes
        self.act_func = act_func
        self.scheduler_weight = copy(scheduler)
        self.scheduler_bias = copy(scheduler)

        self.weights = None
        self.a_matrix = None
        self.z_matrix = None

    def _feedforward(self, X):
        if len(X.shape) == 1:
            X = X.reshape((1, X.shape[0]))

        self.z_matrix = X @ self.weights

        self.a_matrix = self.act_func(self.z_matrix)
        bias = np.ones((X.shape[0], 1)) * 0.01
        self.a_matrix = np.hstack([bias, self.a_matrix])

        return self.a_matrix

    def _backpropagate(self, weights_next, delta_next, a_prev, lam):
        activation_derivative = derivate(self.act_func)

        delta_matrix = (weights_next[1:, :] @ delta_next.T).T * activation_derivative(
            self.z_matrix
        )

        gradient_weights = np.zeros(
            (
                a_prev[:, 1:].shape[0],
                a_prev[:, 1:].shape[1],
                delta_matrix.shape[1],
            )
        )

        for i in range(len(delta_matrix)):
            gradient_weights[i, :, :] = np.outer(a_prev[i, 1:], delta_matrix[i, :])

        gradient_weights = np.mean(gradient_weights, axis=0)
        gradient_bias = np.mean(delta_matrix, axis=0).reshape(1, delta_matrix.shape[1])

        # regularization term
        gradient_weights += self.weights[1:, :] * lam

        update_matrix = np.vstack(
            [
                self.scheduler_bias.update_change(gradient_bias),
                self.scheduler_weight.update_change(gradient_weights),
            ]
        )

        self.weights -= update_matrix

        return self.weights, delta_matrix

    def _reset_weights(self, prev_nodes):
        if self.seed is not None:
            np.random.seed(self.seed)

        # if not self.is_first_layer:
        bias = 1
        self.weights = np.random.randn(prev_nodes + bias, self.nodes)
        return self.nodes

    def _reset_scheduler(self):
        self.scheduler_weight.reset()
        self.scheduler_bias.reset()

    def get_prev_a(self):
        return self.a_matrix


class OutputLayer(FullyConnectedLayer):
    def __init__(
        self,
        nodes: int,
        output_func: Callable,
        cost_func: Callable,
        scheduler: Scheduler,
        seed=None,
    ):
        super().__init__(nodes, output_func, copy(scheduler), seed)
        self.cost_func = cost_func

        self.weights = None
        self.a_matrix = None
        self.z_matrix = None

        # self._reset_weights()
        self.set_prediction()  # Decides what type of prediction the output layer performs

    def _feedforward(self, X: np.ndarray):
        if len(X.shape) == 1:
            X = X.reshape((1, X.shape[0]))

        # Adding bias to the data
        self.z_matrix = X @ self.weights
        self.a_matrix = self.act_func(self.z_matrix)

        return self.a_matrix

    def _backpropagate(self, target, a_prev, lam):
        # Again, remember that in the OutputLayer the activation function is the output function
        activation_derivative = derivate(self.act_func)

        if self.prediction == "Multi-class":
            delta_matrix = self.a_matrix - target
        else:
            cost_func_derivative = grad(self.cost_func(target))
            delta_matrix = activation_derivative(self.z_matrix) * cost_func_derivative(
                self.a_matrix
            )

        gradient_weights = np.zeros(
            (
                a_prev[:, 1:].shape[0],
                a_prev[:, 1:].shape[1],
                delta_matrix.shape[1],
            )
        )

        for i in range(len(delta_matrix)):
            gradient_weights[i, :, :] = np.outer(a_prev[i, 1:], delta_matrix[i, :])

        gradient_weights = np.mean(gradient_weights, axis=0)
        gradient_bias = np.mean(delta_matrix, axis=0).reshape(1, delta_matrix.shape[1])

        # regularization term
        gradient_weights += self.weights[1:, :] * lam

        update_matrix = np.vstack(
            [
                self.scheduler_bias.update_change(gradient_bias),
                self.scheduler_weight.update_change(gradient_weights),
            ]
        )

        self.weights -= update_matrix

        return self.weights, delta_matrix

    def predict(self, X: np.ndarray, *, threshold=0.5):
        predict = self._feedforward(X)

        if self.prediction == "Binary":
            return np.where(predict > threshold, 1, 0)
        else:
            return predict

    def set_prediction(self):
        if self.act_func.__name__ is None or self.act_func.__name__ == "identity":
            self.prediction = "Regression"
        elif self.act_func.__name__ == "sigmoid" or self.act_func.__name__ == "tanh":
            self.prediction = "Binary"
        else:
            self.prediction = "Mulit-class"

    def _reset_weights(self, prev_nodes):
        if self.seed is not None:
            np.random.seed(self.seed)

        bias = 1
        self.weights = np.random.rand(prev_nodes + bias, self.nodes)

        return self.nodes

    def _reset_scheduler(self):
        self.scheduler_weight.reset()
        self.scheduler_bias.reset()

    def get_prediction(self):
        return self.prediction


class Convolution2DLayer(Layer):
    def __init__(
        self,
        input_channels,  # number of maps the input is split into
        feature_maps,  # also known as feature maps
        kernel_height,
        kernel_width,
        v_stride,
        h_stride,
        pad,
        act_func: Callable,
        seed=None,
    ):
        super().__init__(seed)
        self.input_channels = input_channels
        self.feature_maps = feature_maps
        self.kernel_height = kernel_height
        self.kernel_width = kernel_width
        self.v_stride = v_stride
        self.h_stride = h_stride
        self.pad = pad
        self.act_func = act_func

        self._reset_weights()

    def _reset_weights(self):
        if self.seed is not None:
            np.random.seed(self.seed)

        self.kernel_tensor = np.ndarray(
            (
                self.input_channels,
                self.feature_maps,
                self.kernel_height,
                self.kernel_width,
            )
        )

        for i in range(self.kernel_tensor.shape[0]):
            for j in range(self.kernel_tensor.shape[1]):
                self.kernel_tensor[i, j, :, :] = np.random.rand(
                    self.kernel_height, self.kernel_width
                )

    def _feedforward(self, X):
        """
        X = [batch_size, input_maps, img_height, img_width]
        """

        X_pad = self._padding(X)

        new_height = int(
            np.floor((X_pad.shape[2] - self.kernel_height) / self.v_stride) + (self.kernel_height % 2)
        )
        new_width = int(
            np.floor((X_pad.shape[3] - self.kernel_width) / self.h_stride) + (self.kernel_width % 2)
        )

        output = np.ndarray(
            (
                X.shape[0],
                self.feature_maps,
                new_height,
                new_width,
            )
        )
        # Will need this parameter for backpropagation
        self.output_shape = output.shape

        for img in range(X.shape[0]):
            for chin in range(self.input_channels):
                for fmap in range(self.feature_maps):
                    for x in range(new_height):
                        for y in range(new_width):
                            output[img, fmap, x, y] = np.sum(
                                X_pad[
                                    img,
                                    chin,
                                    (x * self.v_stride) : (x * self.v_stride)
                                    + self.kernel_height,
                                    (y * self.h_stride) : (y * self.h_stride)
                                    + self.kernel_width,
                                ]
                                * self.kernel_tensor[chin, fmap, :, :]
                            )

        """
        for k_x in range(self.kernel_size): 
            for k_y in range(self.kernel_size): 
                output[x, y, chout, img] += self.kernel_tensor[chin, chout, kx, ky] * input[x+k_x, y+k_y, chin, img]
        """
        # Pay attention to the fact that we're not rotating the kernel by 180 degrees when filtering the image in
        # the convolutional layer, as convolution in terms of Machine Learning is a procedure known as cross-correlation
        # in image processing and signal processing

        return self.act_func(output)

    def _backpropagate(self, X, delta_next):
        # TODO: Fix backprog for stride larger than one
        delta = np.zeros((X.shape))
        print(delta.shape)
        kernel_grad = np.zeros((self.kernel_tensor.shape))

        X_pad = self._padding(X)

        # Since an activation function is used at the output of the convolution layer, its derivative
        # has to be accounted for in the backpropagation -> as if ReLU a layer on its own.
        act_derivative = derivate(self.act_func)
        delta_next = act_derivative(delta_next)

        # The gradient received from the next layer also needs to be padded
        delta_next = self._padding(delta_next)
        print(delta_next.shape)

        for img in range(X.shape[0]):
            for chin in range(self.input_channels):
                for fmap in range(self.feature_maps):
                    for x in range(0, X.shape[2], self.v_stride):
                        for y in range(0, X.shape[3], self.h_stride):
                            delta[img, chin, x, y] = np.sum(
                                delta_next[
                                    img,
                                    fmap,
                                    x : x + self.kernel_height,
                                    y : y + self.kernel_width,
                                ]
                                * np.rot90(
                                    np.rot90(self.kernel_tensor[chin, fmap, :, :])
                                )
                            )

                            for k_x in range(self.kernel_height):
                                for k_y in range(self.kernel_width):
                                    kernel_grad[chin, fmap, k_x, k_y] = np.sum(
                                        X_pad[
                                            img,
                                            chin,
                                            x : x + self.kernel_height,
                                            y : y + self.kernel_width,
                                        ]
                                        * delta_next[
                                            img,
                                            fmap,
                                            x : x + self.kernel_height,
                                            y : y + self.kernel_width,
                                        ]
                                    )
                                    # Each filter is updated
                    self.kernel_tensor[chin, fmap, :, :] -= kernel_grad[
                        chin, fmap, :, :
                    ]

        return delta

    def _padding(self, batch):
        # TODO: Need fixing to output so the channels are merged back together after padding is finished!

        if self.pad == "same":
            new_height = batch.shape[2] + (self.kernel_height // 2) * 2
            new_width = batch.shape[3] + (self.kernel_width // 2) * 2
            hk_height = self.kernel_height // 2
            hk_width = self.kernel_width // 2

            new_tensor = np.ndarray(
                (batch.shape[0], batch.shape[1], new_height, new_width)
            )

            for img in range(batch.shape[0]):
                padded_img = np.zeros((batch.shape[1], new_height, new_width))
                padded_img[
                    :,
                    hk_height : new_height - hk_height,
                    hk_width : new_width - hk_width,
                ] = batch[img, :, :, :]
                new_tensor[img, :, :, :] = padded_img[:, :, :]

            return new_tensor

        else:
            return batch


class Convolution2DLayerOPT(Convolution2DLayer):
    def __init__(
        self,
        input_channels,  # number of maps the input is split into
        feature_maps,  # also known as feature maps
        kernel_height,
        kernel_width,
        v_stride,
        h_stride,
        pad,
        act_func: Callable,
        seed=None,
    ):
        super().__init__(
            input_channels,
            feature_maps,
            kernel_height,
            kernel_width,
            v_stride,
            h_stride,
            pad,
            act_func,
            seed,
        )

    def _extract_windows(self, batch, batch_type="image"):
        # pad the images
        # TODO: Change padding so that it takes the height and width of kernel as arguments
        batch_pad = self._padding(batch)

        windows = []
        img_height, img_width = batch_pad.shape[2:]
        if batch_type == "image":
            # For each location in the image...
            for h in range( img_height - self.kernel_height + self.kernel_height % 2):
                for w in range( img_width - self.kernel_width + self.kernel_width % 2):
                    # ...get an image patch of size [fil_size, fil_size]

                    window = batch_pad[
                        :,
                        :,
                        h : h + self.kernel_height,
                        w : w + self.kernel_width,
                    ]
                    windows.append(window)
            return np.stack(windows)

        if batch_type == "grad":
            for h in range(img_height - self.kernel_height + self.kernel_height % 2):
                for w in range(img_width - self.kernel_width + self.kernel_width % 2):
                    # ...get an image patch of size [fil_size, fil_size]

                    if self.v_stride == 1 and self.h_stride == 1:
                        window = batch_pad[
                            :, :, h : h + self.kernel_height, w : w + self.kernel_width
                        ]
                        windows.append(window)
                    else:
                        # TODO: This functionality needs improvement for asymmetric kernels
                        window = batch_pad[
                            :, :, h : h + self.v_stride, w : w + self.h_stride
                        ]
                        # rest = self.kernel_height % self.v_stride
                        # window = values[
                            # :,
                            # :,
                            # : values.shape[2] - self.v_stride + rest,
                            # : values.shape[3] - self.v_stride + rest,
                        # ]

                        ind = 1
                        for i in range(self.kernel_height // self.v_stride):
                            for j in range(self.h_stride - 1):
                                window = np.insert(window, ind, 0, axis=2)
                            for i in range(self.v_stride - 1):
                                window = np.insert(window, ind, 0, axis=3)
                            ind += self.v_stride

                        # window = window[:,:,:self.kernel_height, :self.kernel_width]
                        windows.append(window)

            return np.stack(windows)

    def _feedforward(self, batch):

        kernel = self.kernel_tensor

        new_height = int(
            np.floor(
                (batch.shape[2] + ((self.kernel_height // 2) * 2) - self.kernel_height)
                / self.v_stride
            )
            + 1
        )
        new_width = int(
            np.floor(
                (batch.shape[3] + ((self.kernel_height // 2) * 2) - self.kernel_width)
                / self.h_stride
            )
            + 1
        )

        print(new_height, new_width)
        windows = self._extract_windows(batch)
        print(windows.shape)
        windows = windows.transpose(1, 0, 2, 3, 4).reshape(
            batch.shape[0],
            new_height * new_width,
            -1,
        )
        print(windows.shape)
        kernel = kernel.transpose(0, 2, 3, 1).reshape(
            kernel.shape[0] * kernel.shape[2] * kernel.shape[3],
            -1,
        )
        output = (windows @ kernel).reshape(
            batch.shape[0],
            new_height,
            new_width,
            -1,
        )
        # The output is reshaped and rearranged to appropriate shape
        return self.act_func(output.transpose(0, 3, 1, 2) / 9)

    def _backpropagate(self, batch, output_grad):
        act_derivative = derivate(self.act_func)
        output_grad = act_derivative(output_grad)

        new_height = int(
            np.floor(
                (batch.shape[2] + ((self.kernel_height // 2) * 2) - self.kernel_height)
                / self.v_stride
            )
            + self.kernel_height % 2
        )
        new_width = int(
            np.floor(
                (batch.shape[3] + ((self.kernel_height // 2) * 2) - self.kernel_width)
                / self.h_stride
            )
            + self.kernel_width % 2
        )
        print(new_height, new_width)
        kernel = self.kernel_tensor

        windows = self._extract_windows(batch, "image").reshape(
            batch.shape[0] * new_height * new_width, -1
        )

        output_grad_tr = output_grad.transpose(0, 2, 3, 1).reshape(
            batch.shape[0] * new_height * new_width, -1
        )

        print(windows.shape)
        print("here")
        print(output_grad_tr.shape)

        kernel_grad = (
            (windows.T @ output_grad_tr)
            .reshape(kernel.shape[0], kernel.shape[2], kernel.shape[3], kernel.shape[1])
            .transpose(0, 3, 1, 2)
        )

        # Computing the input gradient
        windows_out = self._extract_windows(output_grad)

        print(f'{windows_out.shape=}')

        windows_out = windows_out.transpose(1, 0, 2, 3, 4).reshape(
                batch.shape[0] * batch.shape[2] * batch.shape[3],
            -1,
        )
        print(f'{windows_out.shape=}')

        kernel_r = kernel.reshape(self.input_channels, -1)

        input_grad = (windows_out @ kernel_r.T)
        
        print(input_grad.shape)
        import sys 
        sys.exit()

        # .reshape(
        #     batch.shape[0], batch.shape[2], batch.shape[3], kernel.shape[0]
        # )
        input_grad = input_grad.transpose(0, 3, 1, 2)

        # Update the weights in the kernel
        self.kernel_tensor -= kernel_grad

        # Output the gradient to propagate backwards
        return input_grad


class Pooling2DLayer(Layer):
    def __init__(
        self, kernel_height, kernel_width, v_stride, h_stride, pooling="max", seed=2023
    ):
        super().__init__(seed)
        self.kernel_height = kernel_height
        self.kernel_weight = kernel_width
        self.v_stride = v_stride
        self.h_stride = h_stride
        self.pooling = pooling

    def _feedforward(self, X):
        # Saving the input shape for use in the backwardpass
        self.input_shape = X.shape

        # Computing the size of the feature maps based on kernel size and the stride parameter
        new_height = (X.shape[2] - self.kernel_height) // self.v_stride + 1
        if X.shape[2] == X.shape[3]:
            new_width = new_height
        else:
            new_width = (X.shape[2] - self.kernel_width) // self.h_stride + 1

        output = np.ndarray((X.shape[0], X.shape[1], new_height, new_width))

        if self.pooling == "max":
            self.pooling_action = np.max
        elif self.pooling == "average":
            self.pooling_action = np.mean

        for img in range(output.shape[0]):
            for fmap in range(output.shape[1]):
                for x in range(new_height):
                    for y in range(new_width):
                        output[img, fmap, x, y] = self.pooling_action(
                            X[
                                img,
                                fmap,
                                (x * self.v_stride) : (x * self.v_stride)
                                + self.kernel_height,
                                (y * self.h_stride) : (y * self.h_stride)
                                + self.kernel_width,
                            ]
                        )

        return output

    def _backpropagate(self, delta_next, X=[]):
        delta_input = np.zeros((self.input_shape))

        for img in range(delta_next.shape[0]):
            for fmap in range(delta_next.shape[1]):
                for x in range(delta_next.shape[2]):
                    for y in range(delta_next.shape[3]):
                        if self.pooling == "max":
                            window = X[
                                img,
                                fmap,
                                (x * self.v_stride) : (x * self.v_stride)
                                + self.kernel_height,
                                (y * self.h_stride) : (y * self.h_stride)
                                + self.kernel_width,
                            ]

                            i, j = np.unravel_index(window.argmax(), window.shape)

                            delta_input[
                                img,
                                fmap,
                                (x * self.v_stride) + i,
                                (y * self.h_stride) + j,
                            ] += delta_next[img, fmap, x, y]

                        if self.pooling == "average":
                            delta_input[
                                img,
                                fmap,
                                (x * self.v_stride) : (x * self.v_stride)
                                + self.kernel_height,
                                (y * self.h_stride) : (y * self.h_stride)
                                + self.kernel_width,
                            ] = (
                                delta_next[img, fmap, x, y]
                                / self.kernel_height
                                / self.kernel_width
                            )
        return delta_input


class FlattenLayer(Layer):
    def __init__(self, seed=None):
        super().__init__(seed)

    def _feedforward(self, batch):
        self.input_shape = batch.shape
        # Remember, the data has the following shape: (B, FM, H, W, ) Where FM = Feature maps, B = Batch size, H = Height and W = Width
        X_batch = batch.reshape(1, batch.shape[0] * batch.shape[1] * batch.shape[2])
        bias = np.ones((X_batch.shape[0], 1)) * 0.01
        self.a_matrix = np.hstack([bias, X_batch])
        return self.a_matrix

    def _backpropagate(self, delta_next):
        return delta_next.reshape(self.input_shape)

    def get_prev_a(self):
        return self.a_matrix

    def _reset_weights(self, prev_nodes):
        pass
