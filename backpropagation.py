import numpy as np
import inputlayer
import hiddenlayer
import outputlayer

tol = 0.000000000001


def _ReLU(X):
    def int_ReLU(x):
        return x * (x > 0)

    vec = np.vectorize(int_ReLU)
    return vec(X)


def _dReLU(X):
    def int_dReLU(x):
        return 1. * (x > 0)

    vec = np.vectorize(int_dReLU)
    return vec(X)


def _derivative_sigmoid(p_X):
    return _sigmoid(p_X) * (1 - _sigmoid(p_X))


def _sigmoid(X):
    def int_sigmoid(x):
        if x < -100:
            return tol
        elif x > 100:
            return 100 - tol
        else:
            return 1 / (1 + np.exp(-x))

    vect = np.vectorize(int_sigmoid)
    return vect(X)


def _calculate_sigma_output(p_Y_training, v_Y_layer_):
    return np.subtract(p_Y_training, _sigmoid(v_Y_layer_)) * _derivative_sigmoid(v_Y_layer_)


def _calculate_sigma(sigma_U, w_U, v_Y_layer_):
    return (np.dot(sigma_U, w_U.T[:, 1:])) * _dReLU(v_Y_layer_)


def get_accuracy(predicted, test):
    n_hits = len([1 for predicted, expected in zip(predicted, test) if predicted == expected])
    return round(n_hits * 100 / len(test), 2)


def _calculate_delta(eta, sigma, v_Y_previous_layer_):
    delta_w = eta * np.dot(sigma.T, v_Y_previous_layer_)
    delta_w0 = eta * sigma.T
    return np.hstack([delta_w0, delta_w])


class BackPropagation(object):
    """Class BackPropagation:
       Attributes:
         eta.- Learning rate
         number_iterations.-
         random_state.- Random process seed
         input_layer_.-
         hidden_layers_.-
         output_layer_.-
         sse_while_fit_.-
       Methods:
         __init__(p_eta=0.01, p_iterations_number=50, p_ramdon_state=1)
         fit(p_X_training, p_Y_training, p_X_validation, p_Y_validation,
             p_number_hidden_layers=1, p_number_neurons_hidden_layers=np.array([1]))
         predict(p_x) .- Method to predict the output, y
    """

    def __init__(self, p_eta=0.01, p_number_iterations=50, p_random_state=None):
        self.eta = p_eta
        self.number_iterations = p_number_iterations
        self.random_seed = np.random.RandomState(p_random_state)
        self.sse_list = []
        self.accuracy_list = []

    def fit(self, p_X_training,
            p_Y_training,
            p_X_validation,
            p_Y_validation,
            p_batchs_per_epoch=50,
            p_number_hidden_layers=1,
            p_number_neurons_hidden_layers=np.array([1])):

        print("Porcentaje de accidentes: ", round(np.mean(p_Y_training[:, 0]) * 100, 2), "%\n")

        self.input_layer_ = inputlayer.InputLayer(p_X_training.shape[1])
        self.hidden_layers_ = []
        for v_layer in range(p_number_hidden_layers):
            if v_layer == 0:
                self.hidden_layers_.append(hiddenlayer.HiddenLayer(p_number_neurons_hidden_layers[v_layer],
                                                                   self.input_layer_.number_neurons))
            else:
                self.hidden_layers_.append(hiddenlayer.HiddenLayer(p_number_neurons_hidden_layers[v_layer],
                                                                   p_number_neurons_hidden_layers[v_layer - 1]))

        self.output_layer_ = outputlayer.OutputLayer(p_Y_training.shape[1],
                                                     self.hidden_layers_[
                                                         self.hidden_layers_.__len__() - 1].number_neurons)

        self.input_layer_.init_w(self.random_seed)
        for v_hidden_layer in self.hidden_layers_:
            v_hidden_layer.init_w(self.random_seed)
        self.output_layer_.init_w(self.random_seed)

        randomize = np.arange(len(p_X_training))
        p_X_shuffle = p_X_training.copy()
        p_Y_shuffle = p_Y_training.copy()
        for epoch in range(0, self.number_iterations):
            np.random.shuffle(randomize)
            p_X_training = p_X_shuffle[randomize]  # pX[2], pX[1], pX[0]
            p_Y_training = p_Y_shuffle[randomize]  # pY[2], py[1], py[0]
            if p_batchs_per_epoch > len(p_X_training):
                p_batchs_per_epoch = len(p_X_training)

            for batch in range(0, p_batchs_per_epoch):
                current_batch_X = p_X_training[batch:batch + 1, :]
                current_batch_Y = p_Y_training[batch:batch + 1, :]

                # FORWARD
                v_Y = []  # vector of net_input results of each layer
                z_Y = []  # vector of activation results of each layer
                w = []  # vector of weights of each layer

                v_Y.append(self.input_layer_._net_input(current_batch_X))
                z_Y.append(self.input_layer_._activation(v_Y[-1]))
                w.append(self.input_layer_.w)
                for v_hiddenlayer in self.hidden_layers_:
                    v_Y.append(v_hiddenlayer._net_input(z_Y[-1]))
                    z_Y.append(v_hiddenlayer._activation(v_Y[-1]))
                    w.append(v_hiddenlayer.w)
                v_Y.append(self.output_layer_._net_input(z_Y[-1]))
                w.append(self.output_layer_.w)

                # BACKWARD
                sigma = _calculate_sigma_output(current_batch_Y, v_Y.pop())
                delta_w = _calculate_delta(self.eta, sigma, z_Y.pop())
                self.output_layer_.w = self.output_layer_.w + delta_w.T
                sigma_U = sigma
                for i in reversed(range(0, len(self.hidden_layers_))):
                    sigma = _calculate_sigma(sigma_U, w.pop(), v_Y.pop())
                    delta_w = _calculate_delta(self.eta, sigma, z_Y.pop())
                    self.hidden_layers_[i].w += delta_w.T
                    sigma_U = sigma

            sse = np.mean(np.square(np.subtract(p_Y_validation, self.get_act_value(p_X_validation))))
            accuracy = get_accuracy(self.predict(p_X_validation), p_Y_validation)
            self.sse_list.append(sse)
            self.accuracy_list.append(accuracy)
            print("\rIteracion %s: ACC: %f\tSSE: %f\t\t\t" % (epoch, accuracy, sse), end='')

        return self

    def predict(self, p_X):
        v_Y_input_layer_ = self.input_layer_.predict(p_X)
        v_X_hidden_layer_ = v_Y_input_layer_
        for v_hiddenlayer in self.hidden_layers_:
            v_Y_hidden_layer_ = v_hiddenlayer.predict(v_X_hidden_layer_)
            v_X_hidden_layer_ = v_Y_hidden_layer_
        v_X_output_layer_ = v_Y_hidden_layer_
        v_Y_output_layer_ = self.output_layer_.predict(v_X_output_layer_)
        return v_Y_output_layer_

    def get_act_value(self, p_X):
        v_Y_input_layer_ = self.input_layer_.predict(p_X)
        v_X_hidden_layer_ = v_Y_input_layer_
        for v_hiddenlayer in self.hidden_layers_:
            v_Y_hidden_layer_ = v_hiddenlayer.predict(v_X_hidden_layer_)
            v_X_hidden_layer_ = v_Y_hidden_layer_
        v_X_output_layer_ = v_Y_hidden_layer_
        v_Y_output_layer_ = self.output_layer_.activate(v_X_output_layer_)
        return v_Y_output_layer_
