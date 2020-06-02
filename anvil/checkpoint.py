"""
checkpoint.py

Module for loading neural networks and checkpoints - ensuring a copy of model
is made so that we don't get unexpected results

"""
from copy import deepcopy

from reportengine import collect

from anvil.models import normalising_flow

model = normalising_flow#collect("normalising_flow", ("mixture_indices",))

def loaded_checkpoint(checkpoint):
    if checkpoint is None:
        return None
    cp_loaded = checkpoint.load()
    return cp_loaded


def train_range(loaded_checkpoint, epochs):
    if loaded_checkpoint is not None:
        cp_epoch = loaded_checkpoint["epoch"]
        train_range = (cp_epoch, cp_epoch + epochs)
    else:
        train_range = (0, epochs)
    return train_range


def loaded_model(loaded_checkpoint, model):
    new_model = deepcopy(model)  # need to copy model so we don't get weird results
    if loaded_checkpoint is not None:
        new_model.load_state_dict(loaded_checkpoint["model_state_dict"])
    return new_model


def current_loss(loaded_checkpoint):
    if loaded_checkpoint is None:
        return None
    return loaded_checkpoint["loss"]
