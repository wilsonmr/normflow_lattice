# SPDX-License-Identifier: GPL-3.0-or-later
# Copywrite © 2021 anvil Michael Wilson, Joe Marsh Rossney, Luigi Del Debbio
"""
models.py

Module containing reportengine actions which return callable objects that execute
normalising flows constructed from multiple layers via function composition.
"""
import torch
from functools import partial
from reportengine import collect

from anvil.core import Sequential
import anvil.layers as layers


def coupling_block(coupling_layer, size_half, **layer_spec):
    """Helper function which returns a callable object that performs a coupling
    transformation on both even and odd lattice sites."""
    coupling_transformation = partial(coupling_layer, size_half, **layer_spec)
    return Sequential(
        coupling_transformation(even_sites=True),
        coupling_transformation(even_sites=False),
    )


def real_nvp(
    size_half,
    n_affine,
    hidden_shape,
    activation="tanh",
    z2_equivar=False,
):
    """Action that returns a callable object that performs a sequence of `n_affine`
    affine coupling transformations on both partitions of the input vector."""
    blocks = [
        coupling_block(
            layers.AffineLayer,
            size_half,
            hidden_shape=hidden_shape,
            activation=activation,
            z2_equivar=z2_equivar,
        )
        for i in range(n_affine)
    ]
    return Sequential(*blocks, layers.GlobalRescaling())


def nice(
    size_half,
    n_additive,
    hidden_shape,
    activation="tanh",
    z2_equivar=False,
):
    """Action that returns a callable object that performs a sequence of `n_affine`
    affine coupling transformations on both partitions of the input vector."""
    blocks = [
        coupling_block(
            layers.AdditiveLayer,
            size_half,
            hidden_shape=hidden_shape,
            activation=activation,
            z2_equivar=z2_equivar,
        )
        for i in range(n_additive)
    ]
    return Sequential(*blocks, layers.GlobalRescaling())


def rational_quadratic_spline(
    size_half,
    hidden_shape,
    interval=5,
    n_spline=1,
    n_segments=4,
    activation="tanh",
    z2_equivar_spline=False,
):
    """Action that returns a callable object that performs a block of circular spline
    transformations, one on each half of the input vector."""
    blocks = [
        coupling_block(
            layers.RationalQuadraticSplineLayer,
            size_half,
            interval=interval,
            n_segments=n_segments,
            hidden_shape=hidden_shape,
            activation=activation,
            z2_equivar=z2_equivar_spline,
        )
        for _ in range(n_spline)
    ]
    return Sequential(
        #layers.BatchNormLayer(),
        *blocks,
        layers.GlobalRescaling(),
    )


def spline_affine(real_nvp, rational_quadratic_spline):
    return Sequential(*rational_quadratic_spline, *real_nvp)


def affine_spline(real_nvp, rational_quadratic_spline):
    return Sequential(*real_nvp, *rational_quadratic_spline)

# TODO replace this
_loaded_model = collect("loaded_model", ("training_context",))


def model_weights(_loaded_model):
    model = _loaded_model[0]

    for block in model:
        params = {
            key: tensor.flatten().numpy() for key, tensor in block.state_dict().items()
        }
        if len(params) > 1:  # only want coupling layers
            yield params

MODEL_OPTIONS = {
    "nice": nice,
    "real_nvp": real_nvp,
    "rational_quadratic_spline": rational_quadratic_spline,
    "spline_affine": spline_affine,
    "affine_spline": affine_spline,
}
