import os
import json
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_file = Path(__file__).resolve().parent / '.env'
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        os.environ.setdefault(k.strip(), v.strip())
        except Exception:
            pass

BASE_DIR = Path(__file__).resolve().parent

# Source-of-truth Room loading
ROOMS = []
rooms_path = BASE_DIR / 'rooms.json'
if rooms_path.exists():
    try:
        with open(rooms_path, 'r', encoding='utf-8') as f:
            room_defs = json.load(f)
            for r in room_defs:
                room_entry = {
                    'name': r['name'],
                    'display_name': r.get('display_name', r['name'])
                }
                if 'participant_label_file' in r:
                    label_file = BASE_DIR / r['participant_label_file']
                    if label_file.exists():
                        room_entry['participant_label_file'] = str(label_file)
                ROOMS.append(room_entry)
    except Exception as e:
        print(f"[Warning] Failed loading rooms.json: {e}")

SESSION_CONFIGS = [
    {
        'name': 'modal_shift',
        'display_name': 'Modal Shift & Carbon Taxation (Main Experiment)',
        'app_sequence': [
            'intro',
            'commute_choice',
            'survey_demographics',
            'survey_traits',
            'post_task'
        ],
        'treatment_assignment': 'balanced_random',
        'language': 'en',
        'num_demo_participants': 30,
        'doc': """
        Main between-subject experiment with 3 balanced treatments:
        - Treatment A: Control commute costs
        - Treatment B: Loss framing (+€30 Carbon Surcharge on car)
        - Treatment C: Gain framing (-€30 Green Mobility Voucher on public transit)
        Net financial advantage of transit over car is strictly identical in B and C (+€30 vs control).
        """
    },
    {
        'name': 'modal_shift_surveys_first',
        'display_name': 'Modal Shift (Surveys First - Pre-Treatment Traits)',
        'app_sequence': [
            'intro',
            'survey_demographics',
            'survey_traits',
            'commute_choice',
            'post_task'
        ],
        'treatment_assignment': 'balanced_random',
        'language': 'en',
        'num_demo_participants': 30,
        'doc': """
        Methodological variant where demographic and psychological trait surveys
        are administered before the choice task, isolating pre-treatment traits
        from potential task-induced priming or post-treatment bias.
        """
    },
    {
        'name': 'modal_shift_A',
        'display_name': 'Modal Shift - Branch A (Control Only)',
        'app_sequence': [
            'intro',
            'commute_choice',
            'survey_demographics',
            'survey_traits',
            'post_task'
        ],
        'treatment_assignment': 'fixed',
        'fixed_treatment': 'A',
        'language': 'en',
        'num_demo_participants': 6,
        'doc': 'Fixed single-branch session: Control condition only.'
    },
    {
        'name': 'modal_shift_B',
        'display_name': 'Modal Shift - Branch B (Loss / Carbon Penalty Only)',
        'app_sequence': [
            'intro',
            'commute_choice',
            'survey_demographics',
            'survey_traits',
            'post_task'
        ],
        'treatment_assignment': 'fixed',
        'fixed_treatment': 'B',
        'language': 'en',
        'num_demo_participants': 6,
        'doc': 'Fixed single-branch session: Loss framing (Carbon tax on car) only.'
    },
    {
        'name': 'modal_shift_C',
        'display_name': 'Modal Shift - Branch C (Gain / Green Bonus Only)',
        'app_sequence': [
            'intro',
            'commute_choice',
            'survey_demographics',
            'survey_traits',
            'post_task'
        ],
        'treatment_assignment': 'fixed',
        'fixed_treatment': 'C',
        'language': 'en',
        'num_demo_participants': 6,
        'doc': 'Fixed single-branch session: Gain framing (Mobility voucher on transit) only.'
    }
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00,
    participation_fee=0.00,
    doc=""
)

PARTICIPANT_FIELDS = [
    'treatment',
    'scenario_order',
    'is_bot',
    'persona'
]

SESSION_FIELDS = []

LANGUAGE_CODE = 'en'
REAL_WORLD_CURRENCY_CODE = 'EUR'
USE_POINTS = False

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = os.environ.get('OTREE_ADMIN_PASSWORD', 'admin')

DEMO_PAGE_INTRO_HTML = """
<h3>Modal Shift and Carbon Taxation</h3>
<p>
    Experimental study evaluating how financial framing (Loss: Carbon Tax vs Gain: Clean Mobility Voucher)
    affects commuters' mode choice under strictly equivalent net financial advantages.
</p>
"""

SECRET_KEY = os.environ.get('OTREE_SECRET_KEY', '57a46977-9430-4e3a-b8cb-469b6e680a6c')
DEBUG = os.environ.get('DEBUG', '0') == '1'

