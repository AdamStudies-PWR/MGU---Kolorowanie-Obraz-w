import os
import shutil
import sys
import torch

import numpy as np

from PIL import Image
from skimage.color import lab2rgb
from torchvision import transforms

from Utilities.model import Network


MODEL_FOLDER = "model"
MODEL_PATH = os.path.join(MODEL_FOLDER, "model.pt")
RESULT_PATH = "result"


def get_images(batch, cpu):
    batch = (batch + 1.) * 50.
    cpu = cpu * 110.
    batch = torch.cat([batch, cpu], dim=1).permute(0, 2, 3, 1).cpu().numpy()
    images = []
    for img in batch:
        img = lab2rgb(img)
        images.append(img)
    return images


args = sys.argv

if len(args) <= 1:
    print("No path provided - aborting!")
    exit(0)

path = args[1]

if not os.path.exists(path) and not os.path.isfile(path):
    print("Invalid path")
    exit(0)

if not os.path.exists(MODEL_PATH) and not os.path.isfile(MODEL_PATH):
    print("Model does not exist - run train.py first")
    exit(0)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Loading model...")
model = Network()
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))

img = Image.open(path)
tensor = transforms.ToTensor()(img)[:1] * 2. - 1.
model.eval()

print("Colorizning image...")
with torch.no_grad():
    predicates = model.unet(tensor.unsqueeze(0).to(device))
colorized = get_images(tensor.unsqueeze(0), predicates.cpu())

print("Saving result...")

if os.path.exists(RESULT_PATH):
    shutil.rmtree(RESULT_PATH)
os.mkdir(RESULT_PATH)

filename = os.path.basename(path)
filename = os.path.join(RESULT_PATH, filename)
counter = 0
for img in colorized:
    img = img * 255
    img = Image.fromarray(np.uint8(img))
    img.save(filename + "-colorized" + str(counter) + ".png")
    counter = counter + 1

print("Finished")
