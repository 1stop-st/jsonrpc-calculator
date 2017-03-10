#
# The data structure of 'model' is below:
#
#     'nodes' : { id(hashable): { x:Real, y:Real, z:Real } }
#     'lines' : { id(hashable): { n1:id, n2:id, EA:Real } }
#     'boundaries' : { id(hashable): { node:id, x:Real or Bool, y:Real or Bool, z:Real or Bool, rx:Real or Bool, ry:Real or Bool, rz:Real or Bool } }
#     'nodeLoads' : { id(hashable): { node:id, x:Real, y:Real, z:Real, rx:Real, ry:Real, rz:Real } }
#

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from scipy.linalg import solve
from frame import line, section
from frame.model import Model


def values(seq):
    iters = seq.values() if isinstance(seq, dict) else seq
    for value in iters:
        if value is not None:
            yield value


def items(seq):
    iters = seq.items() if isinstance(seq, dict) else enumerate(seq)
    for key, value in iters:
        if value is not None:
            yield key, value


def keys(seq):
    for key, _ in items(seq):
        yield key


def calculate(model):
    coos = 'x', 'y', 'z', 'rx', 'ry', 'rz'
    fixed_coos = {
        (bound['node'], coo)
            for bound in values(model['boundaries'])
                for coo in coos
                    if bound[coo] and isinstance(bound[coo], bool)
    }
    coo_indexes = tuple(
        (node_id, coo)
            for node_id in keys(model['nodes'])
                for coo in coos
                    if (node_id, coo) not in fixed_coos
    )
    sections = {
        id: section.properties(**data)
            for id, data in items(model['sections'])
    }
    materials = model['materials']
    data = []
    rows = []
    cols = []
    ends = 'n1', 'n2'
    perm = ((a, b) for a in ends for b in ends)
    arg_keys = 'Ax', 'Iz', 'Iy', 'Ay', 'Az', 'theta', 'J'
    for ln in values(model['lines']):
        nobjs = tuple(model['nodes'][ln[end]] for end in ends)
        v = tuple(nobjs[1][c] - nobjs[0][c] for c in coos[:3])
        s = {
            key: value
                for key, value in sections[ln['section']].items()
                    if key in arg_keys
        }
        s.update(materials[ln['material']])
        matrixes = line.stiffness_global(*v, **s)
        for k, n in zip(matrixes, perm):
            for i, c1 in enumerate(coos):
                try:
                    row = coo_indexes.index((ln[n[0]], c1))
                except ValueError:
                    continue
                for j, c2 in enumerate(coos):
                    try:
                        col = coo_indexes.index((ln[n[1]], c2))
                    except ValueError:
                        continue
                    data.append(k[i][j])
                    rows.append(row)
                    cols.append(col)
    a = coo_matrix((data, (rows, cols)), shape=(len(coo_indexes),)*2)
    b = np.zeros(len(coo_indexes))
    for ld in values(model['nodeLoads']):
        for coo in coos:
            if ld[coo]:
                try:
                    row = coo_indexes.index((ld['node'], coo))
                except ValueError:
                    continue
                b[row] += ld[coo]
    dis = spsolve(a, b)
    R = {}
    for node_id, coo in coo_indexes:
        if node_id in R:
            R[node_id][coo] = dis[coo_indexes.index((node_id, coo))]
        else:
            R[node_id] = {coo: dis[coo_indexes.index((node_id, coo))]}
    return {
        'displacements': R
    }


def frame_calculate(frameModel):
    inputModel = Model(frameModel, allow_overwrite=True)
    K = np.zeros((inputModel.effective_count(), ) * 2)
    for key, tline in inputModel.lines.items():
        n = (tline['n1'], tline['n2'])
        v = inputModel.line_vector(key)
        E = tline['EA']
        G = 0
        A = 1
        for i, Ki in enumerate(line.stiffness_global(v[0], v[1], v[2], E, G, A)):
            for k1, d1 in enumerate(('x', 'y', 'z', 'rx', 'ry', 'rz')):
                for k2, d2 in enumerate(('x', 'y', 'z', 'rx', 'ry', 'rz')):
                    a = inputModel.effective_indexof(n[i // 2], d1)
                    b = inputModel.effective_indexof(n[i % 2], d2)
                    if a >= 0 and b >= 0:
                        K[a][b] += Ki[k1][k2]
    P = np.zeros(inputModel.effective_count())
    for node_load in inputModel.nodeLoads.values():
        for d in ('x', 'y', 'z', 'rx', 'ry', 'rz'):
            i = inputModel.effective_indexof(node_load['node'], d)
            if i >= 0:
                P[i] += node_load[d]
    D = solve(K, P, overwrite_a=True, overwrite_b=True)
    R = {}
    for node_id, coodinate in inputModel.effective_coodinates():
        if node_id in R:
            R[node_id][coodinate] = D[inputModel.effective_indexof(node_id, coodinate)]
        else:
            R[node_id] = {coodinate: D[inputModel.effective_indexof(node_id, coodinate)]}
    return {'displacements': R}
