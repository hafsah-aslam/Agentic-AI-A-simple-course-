"""Frozen heavy-atom topology matcher from Milestone 2.

The functions below are copied from ``docking_correction.artifact_generation``
without behavioural changes.  They are retained here only so the GPU runner
does not need the full original source tree during downstream scoring.
"""

from __future__ import annotations

import math

import networkx as nx
import numpy as np
from rdkit import Chem


class ArtifactError(RuntimeError):
    """A molecule cannot be matched under the frozen atom-identity contract."""


def _heavy_coords(molecule: Chem.Mol) -> tuple[list[int], np.ndarray]:
    indices = [atom.GetIdx() for atom in molecule.GetAtoms() if atom.GetAtomicNum() > 1]
    conformer = molecule.GetConformer()
    coords = np.asarray(
        [[conformer.GetAtomPosition(index).x, conformer.GetAtomPosition(index).y, conformer.GetAtomPosition(index).z]
         for index in indices],
        dtype=np.float64,
    )
    if len(indices) == 0 or not np.isfinite(coords).all():
        raise ArtifactError("ligand has no finite heavy-atom coordinates")
    return indices, coords


def _heavy_graph(molecule: Chem.Mol) -> tuple[nx.Graph, list[int]]:
    heavy, _coords = _heavy_coords(molecule)
    local = {original: index for index, original in enumerate(heavy)}
    graph = nx.Graph()
    for original, index in local.items():
        graph.add_node(index, element=molecule.GetAtomWithIdx(original).GetSymbol())
    for bond in molecule.GetBonds():
        begin, end = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        if begin in local and end in local:
            graph.add_edge(local[begin], local[end])
    return graph, heavy


def match_reference_pose(reference: Chem.Mol, docked: Chem.Mol) -> tuple[np.ndarray, np.ndarray, float, dict[str, int]]:
    ref_indices, ref_coords = _heavy_coords(reference)
    dock_indices, dock_coords = _heavy_coords(docked)
    if len(ref_indices) != len(dock_indices):
        raise ArtifactError("atom_matching_failed: heavy-atom count mismatch")
    if sorted(reference.GetAtomWithIdx(index).GetSymbol() for index in ref_indices) != sorted(
        docked.GetAtomWithIdx(index).GetSymbol() for index in dock_indices
    ):
        raise ArtifactError("atom_matching_failed: heavy-atom element multiset mismatch")
    ref_graph, _ = _heavy_graph(reference)
    dock_graph, _ = _heavy_graph(docked)
    matcher = nx.algorithms.isomorphism.GraphMatcher(
        dock_graph,
        ref_graph,
        node_match=lambda left, right: left["element"] == right["element"],
    )
    best_rmsd = math.inf
    best_coords: np.ndarray | None = None
    mapping_count = 0
    for mapping in matcher.isomorphisms_iter():
        mapping_count += 1
        candidate = np.empty_like(ref_coords)
        for dock_index, ref_index in mapping.items():
            candidate[ref_index] = dock_coords[dock_index]
        rmsd = float(np.sqrt(np.mean(np.sum((candidate - ref_coords) ** 2, axis=1))))
        if rmsd < best_rmsd:
            best_rmsd = rmsd
            best_coords = candidate
    if best_coords is None:
        raise ArtifactError("atom_matching_failed: no element-typed bond-graph isomorphism")
    return best_coords, ref_coords, best_rmsd, {"isomorphisms_considered": mapping_count}
