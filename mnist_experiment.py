import torch
import torchvision
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import os

class Net(nn.Module):
    def __init__(self, add_batch_norm = False, add_dropout_fn = False, add_dropout_cn = False):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
        self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
        self.add_dropout_fn = add_dropout_fn
        self.add_dropout_cn = add_dropout_cn
        self.add_batch_norm = add_batch_norm
        if self.add_dropout_cn:
            self.conv2_drop = nn.Dropout2d()
        self.fc1 = nn.Linear(320, 50)
        self.fc2 = nn.Linear(50, 10)
        if self.add_batch_norm:
            self.bn1 = nn.BatchNorm2d(10)
            self.bn2 = nn.BatchNorm2d(20)
            self.bn3 = nn.BatchNorm1d(50)

    def forward(self, x):
        if self.add_batch_norm:
            x = F.relu(self.bn1(F.max_pool2d(self.conv1(x), 2)))
            if self.add_dropout_cn:
                x = F.relu(self.bn2(F.max_pool2d(self.conv2_drop(self.conv2(x)), 2)))
            else:
                x = F.relu(self.bn2(F.max_pool2d(self.conv2(x), 2)))
        else:
            x = F.relu(F.max_pool2d(self.conv1(x), 2))
            if self.add_dropout_cn:
                x = F.relu(F.max_pool2d(self.conv2_drop(self.conv2(x)), 2))
            else:
                x = F.relu(F.max_pool2d(self.conv2(x), 2))

        x = x.view(-1, 320)
        if self.add_batch_norm:
            x = F.relu(self.bn3(self.fc1(x)))
        else:
            x = F.relu(self.fc1(x))
        if self.add_dropout_fn:
            x = F.dropout(x, training=self.training)
        else:
            pass
        x = self.fc2(x)
        return F.log_softmax(x)

n_epochs = 3
batch_size_train = 64
batch_size_test = 1000
learning_rate = 0.01
momentum = 0.5
log_interval = 10

random_seed = 1
torch.backends.cudnn.enabled = False
torch.manual_seed(random_seed)

train_loader = torch.utils.data.DataLoader(
  torchvision.datasets.MNIST('./files/', train=True, download=True,
                             transform=torchvision.transforms.Compose([
                               torchvision.transforms.ToTensor(),
                               torchvision.transforms.Normalize(
                                 (0.1307,), (0.3081,))
                             ])),
  batch_size=batch_size_train, shuffle=True)

test_loader = torch.utils.data.DataLoader(
  torchvision.datasets.MNIST('./files/', train=False, download=True,
                             transform=torchvision.transforms.Compose([
                               torchvision.transforms.ToTensor(),
                               torchvision.transforms.Normalize(
                                 (0.1307,), (0.3081,))
                             ])), batch_size=batch_size_test, shuffle=True)

examples = enumerate(test_loader)
batch_idx, (example_data, example_targets) = next(examples)

network = Net(add_batch_norm=False, add_dropout_cn= False, add_dropout_fn=True)
optimizer = optim.SGD(network.parameters(), lr=learning_rate,
                      momentum=momentum)

train_losses = []
train_counter = []
test_losses = []
test_counter = [i*len(train_loader.dataset) for i in range(n_epochs + 1)]

if not os.path.exists('./results'):
    os.system("mkdir -p %s"%'./results')

def train(epoch):
  network.train()
  for batch_idx, (data, target) in enumerate(train_loader):
    optimizer.zero_grad()
    output = network(data)
    loss = F.nll_loss(output, target)
    loss.backward()
    optimizer.step()
    if batch_idx % log_interval == 0:
      print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
        epoch, batch_idx * len(data), len(train_loader.dataset),
        100. * batch_idx / len(train_loader), loss.item()))
      train_losses.append(loss.item())
      train_counter.append(
        (batch_idx*64) + ((epoch-1)*len(train_loader.dataset)))
      if False:
          torch.save(network.state_dict(), './results/model.pth')
          torch.save(optimizer.state_dict(), './results/optimizer.pth')

def test():
  network.eval()
  test_loss = 0
  correct = 0
  with torch.no_grad():
    for data, target in test_loader:
      output = network(data)
      test_loss += F.nll_loss(output, target, size_average=False).item()
      pred = output.data.max(1, keepdim=True)[1]
      correct += pred.eq(target.data.view_as(pred)).sum()
  test_loss /= len(test_loader.dataset)
  test_losses.append(test_loss)
  print('\nTest set: Avg. loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
    test_loss, correct, len(test_loader.dataset),
    100. * correct / len(test_loader.dataset)))

test()
for epoch in range(1, n_epochs + 1):
  train(epoch)
  test()

aaa = 1

