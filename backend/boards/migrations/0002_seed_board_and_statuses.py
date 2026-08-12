from django.db import migrations

# Single project/board for MVP (no multi-project switching, per
# Spadework_Tier2_Kanban_Spec_v1.md) — this migration creates that one
# Board and its four fixed Status columns. `order` is set here, at seed
# time, and is NOT user-editable/reorderable afterward.
FIXED_STATUSES = [
    ('Todo', 0),
    ('In Progress', 1),
    ('Blocked', 2),
    ('Done', 3),
]


def seed_board_and_statuses(apps, schema_editor):
    Board = apps.get_model('boards', 'Board')
    Status = apps.get_model('boards', 'Status')

    board = Board.objects.create(
        name='miniJira Board',
        description='The single project board for miniJira MVP.',
    )
    for name, order in FIXED_STATUSES:
        Status.objects.create(board=board, name=name, order=order)


def remove_seeded_board_and_statuses(apps, schema_editor):
    Board = apps.get_model('boards', 'Board')
    Board.objects.filter(name='miniJira Board').delete()  # cascades to Status


class Migration(migrations.Migration):

    dependencies = [
        ('boards', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_board_and_statuses, remove_seeded_board_and_statuses),
    ]
