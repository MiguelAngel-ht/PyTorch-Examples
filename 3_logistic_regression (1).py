# -*- coding: utf-8 -*-
"""3-logistic-regression.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1nkriD7EgitlfI05-luwK-Ysf3yXvyYBe

# Image Classification with Logistic Regression
"""

# importing libraries
import torch
import torchvision    # pytorch for computer vision 
from torchvision.datasets import MNIST

# to delete output in google colab
from google.colab import output

# download training data
data = MNIST(root = 'data/', 
             download = True)
output.clear()

# amount of data
len(data)

# get test data 
test = MNIST(root = 'data/',
             train = False)
len(test)

# Commented out IPython magic to ensure Python compatibility.
import matplotlib.pyplot as plt
# %matplotlib inline

img, label = data[0]
plt.imshow(img, cmap='gray')
print('Label:', label)

"""We are going to change data to tensor variables."""

import torchvision.transforms as transforms

# download data
data = MNIST(root = 'data/',
             train = True,
             transform = transforms.ToTensor())

# split to images and labels
img, label = data[0]
print(img.shape, label)

# select a region of image and get max and min
print(img[:, 10:15, 10:15])
print(torch.max(img), torch.min(img))

"""Where 0 is black color and 1 is white color."""

plt.imshow(img[0,10:15,10:15], 'gray')
plt.show()

"""## **Training and Validation**



1.   **Training set:** compute the loss and adjust the weights of the model using gradient descent.
2.   **Validation set:** adjust hyperparameters (for example: lr) and pick the best version of the model.
3. **Test set:** used to compare different models or types of modelling approaches and report the final accuracy of the model.


"""

import numpy as np

def split_indices(n, val_pct):
  """
      args:
              n -  number of values       (int)
              val_pct - percent to take   (float)
      return: 
              training set      (array of indices) 
              validation  set   (array of indices)
  """
  # determine size of validation set
  n_val = int(val_pct * n)

  # create random permutation of 0 to n-1
  idxs = np.random.permutation(n)

  # pick first n_val indices for validation set
  return idxs[n_val:], idxs[:n_val]

train_i, val_i = split_indices(n = len(data),
                               val_pct = 0.2)

print(len(train_i), len(val_i))
print('Sample val indices:', val_i[:10])

from torch.utils.data.sampler import SubsetRandomSampler
from torch.utils.data.dataloader import DataLoader

batch_size = 100

# training sampler and data loader
train_sampler = SubsetRandomSampler(train_i)
train_loader = DataLoader(data,
                          batch_size,
                          sampler=train_sampler)

# validation sampler and data loader
val_sampler = SubsetRandomSampler(val_i)
val_loader = DataLoader(data,
                          batch_size,
                          sampler=val_sampler)

"""## **Model**



*   **Logistic regression** is almost identical to linear regression model `( pred = x @ w.t() + b )`
*   We just use `nn.Linear` to create the model instead of defining and initializing the matrices manually.
*   The output is a vector of size 10, with every probability of particular target label (0-9). 


 
"""

import torch.nn as nn

input_size = 28 * 28
num_classes = 10

# logistic regression model
model = nn.Linear(input_size, num_classes)

print(model.weight.shape)
model.weight

print(model.bias.shape)
model.bias

for images, labels in train_loader:
  print(labels)
  print(images.shape)
  outputs = model(images)
  break

"""This error y because we have a shape 1x20x20 but we need a vector of size 784."""

class MnistModel(nn.Module):
  def __init__(self):
    super().__init__()
    self.linear = nn.Linear(input_size, num_classes)

  def forward(self, xb):
    xb = xb.reshape(-1, 784)
    out = self.linear(xb)
    return out

model = MnistModel()

print(model.linear.weight.shape, model.linear.bias.shape)
list(model.parameters())

for images, labels in train_loader:
  outputs = model(images)
  break

print('Outputs shape:', outputs.shape)
print('Sample outputs:\n', outputs[:2].data)

import torch.nn.functional as F

# obtaining softmax of every row
probs = F.softmax(outputs, dim=1)

print('Sample Probabilities:\n', probs[:2].data)
print('Sum:', torch.sum(probs[1]).item())

max_probs, preds = torch.max(probs, dim=1)
print(preds)
print(max_probs)

labels

"""# Evaluation Metric and Loss Function """

def accuracy(l1, l2):
  return torch.sum(l1 == l2).item() / len(l1)

accuracy(preds, labels)

loss_fn = F.cross_entropy

# Loss fof current batch of data
loss = loss_fn(outputs, labels)
print(loss)

"""# Optimizer

Function to update the weights and biases during training. 
"""

learning_rate = 0.001
optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate)

"""# Training the Model"""

def loss_batch(model, loss_func, xb, yb, opt=None, metric=None):
    # calculate loss
    preds = model(xb)
    loss = loss_func(preds, yb)

    if opt:
      # compute gradients
      loss.backward()
      
      # update parameters
      opt.step()

      # reset gradients
      opt.zero_grad()
    
    metric_result = None
    if metric:
      # compute the metric
      metric_result = metric(preds, yb)

    return loss.item(), len(xb), metric_result

def evaluate(model, loss_fn, valid_dl, metric=None):
    with torch.no_grad():
        # pass each batch through the model
        results = [loss_batch(model, loss_fn, xb, yb, metric=metric)
                    for xb, yb in valid_dl]
        # separate losses, counts and metrics
        losses, nums, metrics = zip(*results)
        # total size of the dataset
        total = np.sum(nums)
        # average loss across batches
        avg_loss = np.sum(np.multiply(losses, nums)) / total
        avg_metric = None

        if metric:
          # average of metric across batches
          avg_metric = np.sum(np.multiply(metrics, nums)) / total

    return avg_loss, total, avg_metric

def accuracy(outputs, labels):
  _, preds = torch.max(outputs, dim=1)
  return torch.sum(preds == labels).item() / len(preds)

val_loss, total, val_acc = evaluate(model, loss_fn, val_loader, metric=accuracy)
print('Loss: {:.4f}, Accuracy: {:.4f}'.format(val_loss, val_acc))

def fit(epochs, model, loss_fn, opt, train_dl, valid_dl, metric=None):
    for epoch in range(epochs):
      # training 
      for xb, yb in train_dl:
          loss, _, _ = loss_batch(model, loss_fn, xb, yb, opt)

      # evaluation
      result = evaluate(model, loss_fn, valid_dl, metric)
      val_loss, total, val_metric = result

      # print progress
      if metric:
        print('Epoch [{}/{}], Loss: {:.4f}, {}: {:.4f}'
              .format(epoch+1, epochs, val_loss, metric.__name__, val_metric)) 
      else:
        print('Epoch [{}/{}], Loss: {:.4f}'
              .format(epoch+1, epochs, val_loss))

# Redefine model and optimizer
model = MnistModel()
optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate)

fit(5, model, F.cross_entropy, optimizer, train_loader, val_loader, accuracy)

# plot accuracies

accuracies = [0.6477, 0.7372, 0.7708, 0.7912, 0.8044]

plt.plot(accuracies, '-x')
plt.xlabel('epoch')
plt.ylabel('accuracy')
plt.title('Accuracy vs No. of epochs')
plt.show()

"""# Testing with Individual Images"""

# define test data

test_data = MNIST(root='data/',
                  train=False,
                  transform=transforms.ToTensor())

img, label = test_data[0]
plt.imshow(img[0], cmap='gray')
print('Shape:', img.shape)
print('Label:', label)

img.unsqueeze(0).shape

def predict_image(img, model):
  xb = img.unsqueeze(0)
  yb = model(xb)
  _, preds = torch.max(yb, dim=1)
  return preds[0].item()

img, label = test_data[0]
plt.imshow(img[0], cmap='gray')
print('Label:', label, ', Predicted:', predict_image(img, model))
plt.show()

img, label = test_data[10]
plt.imshow(img[0], cmap='gray')
print('Label:', label, ', Predicted:', predict_image(img, model))
plt.show()