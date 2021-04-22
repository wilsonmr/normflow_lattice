"""
models.py

Module containing reportengine actions which return callable objects that execute
normalising flows constructed from multiple layers via function composition.
"""
from functools import partial

from anvil.core import Sequential

import anvil.layers as layers


def coupling_pair(coupling_layer, i, size_half, **layer_spec):
    """Helper function which returns a callable object that performs a coupling
    transformation on both even and odd lattice sites."""
    coupling_transformation = partial(coupling_layer, i, size_half, **layer_spec)
    return Sequential(
        coupling_transformation(even_sites=True),
        coupling_transformation(even_sites=False),
    )


def real_nvp(
    size_half,
    n_affine,
    hidden_shape=[
        24,
    ],
    activation="tanh",
    s_final_activation=None,
    symmetric_networks=True,
    bnorm=False,
    bn_scale=1.0,
):
    """Action that returns a callable object that performs a sequence of `n_affine`
    affine coupling transformations on both partitions of the input vector."""
    if bnorm == False:
        affine_pairs = [
            coupling_pair(
                layers.AffineLayer,
                i + 1,
                size_half,
                hidden_shape=hidden_shape,
                activation=activation,
                s_final_activation=s_final_activation,
                symmetric_networks=symmetric_networks,
            )
            for i in range(n_affine)
        ]
        return Sequential(*affine_pairs)
    else:
        output = []
        for i in range(n_affine):
            output.append(
                coupling_pair(
                    layers.AffineLayer,
                    i + 1,
                    size_half,
                    hidden_shape=hidden_shape,
                    activation=activation,
                    s_final_activation=s_final_activation,
                    symmetric_networks=symmetric_networks,
                )
            )
            if i < n_affine - 1:
                output.append(layers.BatchNormLayer(bn_scale, learnable=False))
        return Sequential(*output)


def nice(
    size_half,
    n_additive,
    hidden_shape=[
        24,
    ],
    activation="tanh",
    symmetric=True,
    bnorm=False,
    bn_scale=1.0,
):
    """Action that returns a callable object that performs a sequence of `n_affine`
    affine coupling transformations on both partitions of the input vector."""
    if bnorm == False:
        pairs = [
            coupling_pair(
                layers.AdditiveLayer,
                i + 1,
                size_half,
                hidden_shape=hidden_shape,
                activation=activation,
                symmetric=symmetric,
            )
            for i in range(n_additive)
        ]
        return Sequential(*pairs)
    else:
        output = []
        for i in range(n_additive):
            output.append(
                coupling_pair(
                    layers.AdditiveLayer,
                    i + 1,
                    size_half,
                    hidden_shape=hidden_shape,
                    activation=activation,
                    symmetric=symmetric,
                )
            )
            if i < n_additive - 1:
                output.append(layers.BatchNormLayer(bn_scale, learnable=True))
        return Sequential(*output)


def rational_quadratic_spline(
    size_half,
    sigma,
    scale_sigma_before_spline=1,
    n_pairs=1,
    interval=2,
    n_segments=4,
    hidden_shape=[
        24,
    ],
    activation="tanh",
    symmetric_spline=False,
):
    """Action that returns a callable object that performs a pair of circular spline
    transformations, one on each half of the input vector."""
    return Sequential(
        layers.BatchNormLayer(scale=scale_sigma_before_spline * sigma),
        *[
            coupling_pair(
                layers.RationalQuadraticSplineLayer,
                i + 3,
                size_half,
                interval=interval,
                n_segments=n_segments,
                hidden_shape=hidden_shape,
                activation=activation,
                symmetric_spline=symmetric_spline,
            )
            for i in range(n_pairs)
        ],
    )


def spline_affine(
    real_nvp, rational_quadratic_spline, sigma, scale_sigma_before_spline=1
):
    return Sequential(
        layers.BatchNormLayer(scale=scale_sigma_before_spline * sigma),
        rational_quadratic_spline,
        real_nvp,
    )


def affine_spline(
    real_nvp, rational_quadratic_spline, sigma, scale_sigma_before_spline=1
):
    return Sequential(
        real_nvp,
        layers.BatchNormLayer(scale=scale_sigma_before_spline * sigma),
        rational_quadratic_spline,
    )


def spline_sandwich(
    rational_quadratic_spline,
    sigma,
    size_half,
    n_affine,
    hidden_shape=[
        24,
    ],
    activation="tanh",
    s_final_activation=None,
    symmetric_networks=True,
    scale_sigma_before_spline=1,
):
    affine_1 = [
        coupling_pair(
            layers.AffineLayer,
            i + 1,
            size_half,
            hidden_shape=hidden_shape,
            activation=activation,
            s_final_activation=s_final_activation,
            symmetric_networks=symmetric_networks,
        )
        for i in range(n_affine)
    ]
    affine_2 = [
        coupling_pair(
            layers.AffineLayer,
            i + 3,
            size_half,
            hidden_shape=hidden_shape,
            activation=activation,
            s_final_activation=s_final_activation,
            symmetric_networks=symmetric_networks,
        )
        for i in range(n_affine)
    ]
    return Sequential(
        *affine_1,
        layers.BatchNormLayer(scale=scale_sigma_before_spline * sigma),
        rational_quadratic_spline,
        *affine_2,
    )


MODEL_OPTIONS = {
    "real_nvp": real_nvp,
    "rational_quadratic_spline": rational_quadratic_spline,
    "spline_affine": spline_affine,
    "affine_spline": affine_spline,
    "spline_sandwich": spline_sandwich,
    "nice": nice,
}
