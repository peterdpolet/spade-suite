"""
backend/activities/scheduling.py

Forward/backward pass (Critical Path Method) — Module 11, per
Spadework_miniProject_Spec_v1.md. Deliberately the textbook two-pass
DAG traversal: no resource leveling, no calendars, no lag — see the
spec's own "revised scope exclusion" section for why that's a
deliberate boundary, not a shortcut.

Input shape: activities = [{'id': ..., 'planned_duration': ...}, ...]
             dependencies = [{'predecessor': id, 'successor': id}, ...]

Kept independent of any Django models so it can be tested in complete
isolation, same reasoning as issues/ordering.py.
"""


class CycleDetectedError(Exception):
    """Raised when the dependency graph isn't a valid DAG."""
    def __init__(self, involved_ids):
        self.involved_ids = involved_ids
        super().__init__(f'Dependency cycle detected among activities: {involved_ids}')


def topological_order(activity_ids, dependencies):
    """
    Kahn's algorithm. Returns activity ids in topological order.
    Raises CycleDetectedError if any activities can't be ordered —
    those remaining un-orderable ids ARE the cycle (or part of it).
    """
    predecessors_of = {aid: set() for aid in activity_ids}
    successors_of = {aid: set() for aid in activity_ids}
    for dep in dependencies:
        predecessors_of[dep['successor']].add(dep['predecessor'])
        successors_of[dep['predecessor']].add(dep['successor'])

    no_incoming = [aid for aid in activity_ids if not predecessors_of[aid]]
    ordered = []

    while no_incoming:
        node = no_incoming.pop()
        ordered.append(node)
        for successor in list(successors_of[node]):
            predecessors_of[successor].discard(node)
            successors_of[node].discard(successor)
            if not predecessors_of[successor]:
                no_incoming.append(successor)

    if len(ordered) != len(activity_ids):
        remaining = [aid for aid in activity_ids if aid not in ordered]
        raise CycleDetectedError(remaining)

    return ordered


def compute_schedule(activities, dependencies):
    """
    activities: [{'id': int, 'planned_duration': int}, ...]
    dependencies: [{'predecessor': int, 'successor': int}, ...]

    Returns {activity_id: {'early_start', 'early_finish', 'late_start',
    'late_finish', 'float'}}. Raises CycleDetectedError if the graph
    isn't a DAG — validated BEFORE either pass runs, per spec.
    """
    duration_of = {a['id']: a['planned_duration'] for a in activities}
    activity_ids = list(duration_of.keys())

    order = topological_order(activity_ids, dependencies)  # raises on cycle

    predecessors_of = {aid: [] for aid in activity_ids}
    successors_of = {aid: [] for aid in activity_ids}
    for dep in dependencies:
        predecessors_of[dep['successor']].append(dep['predecessor'])
        successors_of[dep['predecessor']].append(dep['successor'])

    early_start = {}
    early_finish = {}
    for aid in order:
        preds = predecessors_of[aid]
        early_start[aid] = max((early_finish[p] for p in preds), default=0)
        early_finish[aid] = early_start[aid] + duration_of[aid]

    project_finish = max(early_finish.values(), default=0)

    late_start = {}
    late_finish = {}
    for aid in reversed(order):
        succs = successors_of[aid]
        late_finish[aid] = min((late_start[s] for s in succs), default=project_finish)
        late_start[aid] = late_finish[aid] - duration_of[aid]

    return {
        aid: {
            'early_start': early_start[aid],
            'early_finish': early_finish[aid],
            'late_start': late_start[aid],
            'late_finish': late_finish[aid],
            'float': late_start[aid] - early_start[aid],
        }
        for aid in activity_ids
    }