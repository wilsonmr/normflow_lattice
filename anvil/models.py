# SPDX-License-Identifier: GPL-3.0-or-later
# Copywrite © 2021 anvil Michael Wilson, Joe Marsh Rossney, Luigi Del Debbio
"""
models.py

Module containing reportengine actions which return normalising flow models.
Generally this involves piecing together components from :py:mod:`anvil.layers`
to produce sequences of transformations.

"""
from functools import partial

from reportengine import collect

import anvil.layers as layers


def _coupling_pair(coupling_layer, **kwargs):
    """Helper function which wraps a pair of coupling layers from
    :py:mod:`anvil.layers` in the module container
    :py:class`anvil.layers.Sequential`. The first transformation layer acts on
    the even sites and the second transformation acts on the odd sites, so one
    of these blocks ensures all sites are transformed as part of an
    active partition.

    """
    coupling_transformation = partial(coupling_layer, **kwargs)
    return layers.Sequential(
        coupling_transformation(even_sites=True),
        coupling_transformation(even_sites=False),
    )


def real_nvp(
    size_half,
    n_blocks,
    hidden_shape,
    activation="tanh",
    z2_equivar=True,
):
    r"""Action which returns a sequence of ``n_blocks`` pairs of
    :py:class:`anvil.layers.AffineLayer` s, followed by a single
    :py:class:`anvil.layers.GlobalRescaling` all wrapped in the module container
    :py:class`anvil.layers.Sequential`.

    The first ``n_blocks`` elements of the outer ``Sequential``
    are ``Sequential`` s containing a pair of ``AffineLayer`` s which
    act on the even and odd sites respectively.

    Parameters
    ----------
    size_half: int
        Inferred from ``lattice_size``, the size of the active/passive
        partitions (which are equal size, `lattice_size / 2`).
    n_blocks: int
        The number of pairs of :py:class:`anvil.layers.AffineLayer`
        transformations.
    hidden_shape: list[int]
        the shape of the neural networks used in the AffineLayer. The visible
        layers are defined by the ``lattice_size``. Typically we have found
        a single hidden layer neural network is effective, which can be
        specified by passing a list of length 1, i.e. ``[72]`` would
        be a single hidden layered network with 72 nodes in the hidden layer.
    activation: str, default="tanh"
        The activation function to use for each hidden layer. The output layer
        of the network is linear (has no activation function).
    z2_equivar: bool, default=True
        Whether or not to impose z2 equivariance. This changes the transformation
        such that the neural networks have no bias term and s(-v) = s(v) which
        imposes a :math:`\mathbb{Z}_2` symmetry.

    Returns
    -------
    real_nvp: anvil.layers.Sequential
        A sequence of affine transformations, which we refer to as a real NVP
        (Non-volume preserving) flow.

    See Also
    --------
    :py:mod:`anvil.neural_network` contains the fully connected neural network class
    as well as valid choices for activation functions.

    """
    blocks = [
        _coupling_pair(
            layers.AffineLayer,
            size_half=size_half,
            hidden_shape=hidden_shape,
            activation=activation,
            z2_equivar=z2_equivar,
        )
        for i in range(n_blocks)
    ]
    return layers.Sequential(*blocks, layers.GlobalRescaling())


def nice(
    size_half,
    n_blocks,
    hidden_shape,
    activation="tanh",
    z2_equivar=True,
):
    r"""Similar to :py:func:`real_nvp`, excepts instead wraps pairs of
    :py:class:`anvil.layers.AdditiveLayer` s followed by a single
    :py:class:`anvil.layers.GlobalRescaling`. The pairs of ``AdditiveLayer`` s
    act on the even and odd sites respectively.

    Parameters
    ----------
    size_half: int
        Inferred from ``lattice_size``, the size of the active/passive
        partitions (which are equal size, `lattice_size / 2`).
    n_blocks: int
        The number of pairs of :py:class:`anvil.layers.AffineLayer`
        transformations.
    hidden_shape: list[int]
        the shape of the neural networks used in the each layer. The visible
        layers are defined by the ``lattice_size``.
    activation: str, default="tanh"
        The activation function to use for each hidden layer. The output layer
        of the network is linear (has no activation function).
    z2_equivar: bool, default=True
        Whether or not to impose z2 equivariance. This changes the transformation
        such that the neural networks have no bias term and s(-v) = s(v) which
        imposes a :math:`\mathbb{Z}_2` symmetry.

    Returns
    -------
    nice: anvil.layers.Sequential
        A sequence of additive transformations, which we refer to as a
        nice flow.

    """
    blocks = [
        _coupling_pair(
            layers.AdditiveLayer,
            size_half=size_half,
            hidden_shape=hidden_shape,
            activation=activation,
            z2_equivar=z2_equivar,
        )
        for i in range(n_blocks)
    ]
    return layers.Sequential(*blocks, layers.GlobalRescaling())


def rational_quadratic_spline(
    size_half,
    hidden_shape,
    interval=5,
    n_blocks=1,
    n_segments=4,
    activation="tanh",
    z2_equivar=False,
):
    """Similar to :py:func:`real_nvp`, excepts instead wraps pairs of
    :py:class:`anvil.layers.RationalQuadraticSplineLayer` s followed by a single
    :py:class:`anvil.layers.GlobalRescaling`. The pairs of RQS's
    act on the even and odd sites respectively.

    Parameters
    ----------
    size_half: int
        inferred from ``lattice_size``, the size of the active/passive
        partitions (which are equal size, `lattice_size / 2`).
    hidden_shape: list[int]
        the shape of the neural networks used in the each layer. The visible
        layers are defined by the ``lattice_size``.
    interval: int, default=5
        the interval within which the RQS applies the transformation, at present
        if a field variable is outside of this region it is mapped to itself
        (i.e the gradient of the transformation is 1 outside of the interval).
    n_blocks: int, default=1
        The number of pairs of :py:class:`anvil.layers.AffineLayer`
        transformations. For RQS this is set to 1.
    n_segments: int, default=4
        The number of segments to use in the RQS transformation.
    activation: str, default="tanh"
        The activation function to use for each hidden layer. The output layer
        of the network is linear (has no activation function).
    z2_equivar: bool, default=False
        Whether or not to impose z2 equivariance. This is only done crudely
        by splitting the sites according to the sign of the sum across lattice
        sites.

    """
    blocks = [
        _coupling_pair(
            layers.RationalQuadraticSplineLayer,
            size_half=size_half,
            interval=interval,
            n_segments=n_segments,
            hidden_shape=hidden_shape,
            activation=activation,
            z2_equivar=z2_equivar,
        )
        for _ in range(n_blocks)
    ]
    return layers.Sequential(
        *blocks,
        layers.GlobalRescaling(),
    )

_normalising_flow = collect("layer_action", ("model_params",))

def model_to_load(_normalising_flow):
    """action which wraps a list of layers in
    :py:class:`anvil.layers.Sequential`. This allows the user to specify an
    arbitrary combination of layers as the model.

    For more information on valid choices for layers, see
    ``anvil.models.LAYER_OPTIONS`` or the various
    functions in :py:mod:`anvil.models` which produce sequences of the layers
    found in :py:mod:`anvil.layers`.

    At present, available transformations are:

        - ``nice``
        - ``real_nvp``
        - ``rational_quadratic_spline``

    You can see their dependencies using the ``anvil`` provider help, e.g.
    for ``real_nvp``:

    .. code::

        $ anvil-sample --help real_nvp
        ...
        < action docstring - poorly formatted>
        ...
        The following resources are read from the configuration:

            lattice_length(int):
        [Used by lattice_size]

            lattice_dimension(int): Parse lattice dimension from runcard
        [Used by lattice_size]

        The following additionl arguments can be used to control the
        behaviour. They are set by default to sensible values:

        n_blocks
        hidden_shape
        activation = tanh
        z2_equivar = True

    ``anvil-train`` will also provide the same information.

    """
    # assume that _normalising_flow is a list of layers, each layer
    # is a sequential of blocks, each block is a pair of transformations
    # which transforms the entire input state - flatten this out, so output
    # is Sequential of blocks
    flow_flat = [block for layer in _normalising_flow for block in layer]
    return layers.Sequential(*flow_flat)

# Update docstring above if you add to this!
LAYER_OPTIONS = {
    "nice": nice,
    "real_nvp": real_nvp,
    "rational_quadratic_spline": rational_quadratic_spline,
}
