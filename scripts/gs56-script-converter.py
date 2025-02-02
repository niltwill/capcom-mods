# Script to convert the structured text (script) files to JSON files and back
# For PW:AA - Dual Destinies (GS5) and PW:AA - Spirit of Justice (GS6)

import argparse
import glob
import json
import re
import os
from concurrent.futures import ProcessPoolExecutor


# Define the mappings for GS5 - PW: AA - Dual Destinies (DD)
# (These are all the mappings that appear in DD)
dd_mapping = {
    "CNTR": "CENTER",
    "ICON PAD_X": "ICN 2",
    "ICON PAD_L": "ICN 4",
    "ICON PAD_R": "ICN 5",
    "ICON PAD_CROSS": "ICN 9",
    "ICON PAD_SLIDE": "ICN 8",
    "E001": "_END_",
    "E003": "w",
    "E004": "JUMP",
    "E005": "c0",
    "E006": "c1",
    "E007": "c2",
    "E008": "c3",
    "E009": "c4",
    "E020": "REG_SET",
    "E021": "B_REG",
    "E022": "B_RAND",
    "E023": "p",
    "E024": "pa",
    "E025": "s",
    "E026": "CALL",
    "E027": "pdm",
    "E028": "FLAG_ON",
    "E029": "FLAG_OFF",
    "E030": "B_FLAG",
    "E031": "SCENE_JUMP",
    "E032": "B_SCE_JUMP",
    "E033": "CALL_EXTERNAL",
    "E037": "REG_ADD",
    "E040": "WND",
    "E041": "MSG",
    #"E042": "",  # not in PC port, appears before "CNTR" (CENTER)
    "E050": "B_FLAGS",
    "E051": "B_FLAGS_SET",
    "E052": "B_SCENE",
    "E053": "MSG_SKIP_INVALID",
    "E054": "msg_se",
    "E056": "COURT_FILE_BTN_VISIBLE",
    "E057": "OP_TITLE",
    "E060": "THUMB_ON",
    "E061": "THUMB_OFF",
    "E062": "THUMB_ON_SCREEN",
    "E065": "FILTER_SET",
    "E066": "FILTER_WAIT",
    "E070": "FADE",
    "E071": "FADE_WAIT",
    "E072": "FADE_BG",
    "E073": "FADE_BG_WAIT",
    "E074": "FADE_MODEL",
    "E075": "FADE_MODEL_WAIT",
    "E077": "FADE_KAISOU_OUT",
    "E078": "FADE_KAISOU_NOCAM_OUT",
    "E081": "BGM_CONTEXT",
    "E082": "BGM_WAIT",
    "E083": "BGM_SWAP",
    "E084": "BGM_FADE_OUT_OF",
    "E085": "BGM_PLAY",
    "E086": "SE_PLAY",
    "E087": "BGM_STOP",
    "E088": "SE_STOP",
    "E089": "BGM_VOLUME",
    "E090": "SE_VOLUME",
    "E091": "BGM_FADE_IN",
    "E092": "BGM_FADE_OUT",
    "E093": "SE_FADE_IN",
    "E094": "SE_FADE_OUT",
    "E097": "SE_WAIT",
    "E098": "SE_KEYOFF",
    "E099": "SE_VOLUME_OF",
    "E100": "ITEM_ADD",
    "E101": "ITEM_REMOVE",
    "E102": "ITEM_REMOVE_ALL",
    "E103": "EVIDENCE_GET",
    "E104": "egw",
    "E105": "EVIDENCE_UPDATE",
    "E106": "ITEM_UPDATE",
    "E107": "B_ITEM",
    "E108": "B_ITEMS",
    "E109": "B_ITEMS_SET",
    "E110": "FADE_KAISOU_OUT2",
    "E111": "FADE_KAISOU_NOCAM_OUT2",
    "E113": "BGM_WAIT_OF",
    "E114": "BGM_PLAY_STAFFROLL",
    "E115": "INV_SET_ANOTHER_CUT",
    "E116": "INV_DETAIL_CAM_SET",
    "E117": "BG_ORNAMENT_FADE_IN",
    "E118": "BG_ORNAMENT_FADE_OUT",
    "E119": "BG_ORNAMENT_FADE_WAIT",
    "E120": "BG_SET",
    "E121": "BG_ORNAMENT",
    "E122": "USE_BG_CAMERA_ONLY",
    "E123": "BG_CHANGE",
    "E124": "SELECT_POTTERY",
    "E125": "CHR_STOP_SE",
    "E127": "CHR_WAIT_ODOROKI",
    "E128": "CHR_ANIME_NOSTART_ODOROKI",
    "E129": "CHR_ANIME_SPECIAL_ODOROKI",
    "E130": "CAM_SET",
    "E131": "CAM_WAIT",
    "E132": "CAM_SET_FRAME",
    "E133": "CAM_RESUME",
    "E134": "CHR_ANIME_ODOROKI",
    "E135": "CHR_POS_SET",
    "E136": "CHR_DEL_2D_OR_3D",
    "E137": "CHR_SET_2D_OR_3D",
    "E138": "CHR_WAIT_WITHOUT_MOT",
    "E139": "CHR_WAIT_EVENT",
    "E140": "CHR_SET",
    "E141": "CHR_DEL",
    "E142": "CHR_BST_SET",
    "E143": "CHR_BST_DEL",
    "E144": "CHR_WAIT",
    "E145": "CHR_ANIME",
    "E146": "CHR_ANIME_SE",
    "E147": "CHR_ANIME_NOSTART",
    "E148": "CHR_SET_NOSTART",
    "E149": "CHR_BST_SET_NOSTART",
    "E150": "CHR_FORCE_MOUSE",
    "E152": "CHR_LOAD",
    "E153": "CHR_UNLOAD",
    "E154": "CHR_POS",
    "E155": "CHR_BST_POS",
    "E156": "CHR_MAT_CHG",
    "E157": "CHR_VISIBLE",
    "E158": "B_CHR_SET",
    "E159": "CHR_PARTS_DISP",
    "E160": "CHR_ANIME_REP",
    "E161": "CHR_UNLOAD_ALL",
    "E162": "CHR_SET_CHILD",
    "E163": "CHR_BST_SET_CHILD",
    "E164": "CHR_ANIME_SPECIAL",
    "E165": "CHR_ANIME_SPECIAL_NO_SE",
    "E166": "GADGET_FADE",
    "E167": "GADGET_ANIME",
    "E168": "GADGET_COLOR",
    "E169": "CHR_MOUTH",
    "E170": "CHR_ALPHA",
    "E172": "MNK_UNLOAD",
    "E173": "MNK_LOAD",
    "E174": "MNK_FORCE_START",
    "E175": "MNK_INDUCTION_DEMO",
    "E176": "MNK_BUTTON",
    "E177": "MNK_LABEL",
    "E178": "MNK_START",
    "E179": "MNK_MSG_SET",
    "E180": "MNK_MSG",
    "E181": "MNK_CHR_SET",
    "E183": "mnp",
    "E184": "mn_seg",
    "E185": "mn_ans",
    "E186": "MNK_CLEAR",
    "E187": "MNK_MSG_INIT",
    "E188": "MNK_START_TUTORIAL",
    "E189": "MNK_TUTORIAL_CURSOR_WAIT",
    "E190": "BIG_FONT",
    "E191": "BIG_FONT_WAIT",
    "E192": "MNK_TEXT_START_TUTORIAL",
    "E193": "MARK_CONFALENCE",
    "E194": "MARK_TSTMNY",
    "E195": "TESTIMONY",
    "E196": "tw",
    "E197": "COURT_IN",
    "E198": "COURT_IN_WAIT",
    "E201": "NOT_GUILTY",
    "E202": "NOT_GUILTY_WAIT",
    "E205": "EXAMINE",
    "E206": "ew",
    "E207": "SCENARIO_MODE",
    "E208": "HAMMER_PLAY",
    "E209": "HAMMER_WAIT",
    "E210": "DEMO_PLAY",
    "E211": "DEMO_WAIT",
    "E212": "pig",
    "E213": "HAMMER_PLAY_STOP_BGM",
    "E214": "NOW_DATA_SET",
    "E215": "MNK_TUTORIAL_CONT_LABEL",
    "E216": "PSY_KOKONE_END",
    "E217": "PSY_KOKONE_CLEAR",
    "E218": "INV_EVI_GOTO",
    "E220": "CHOICE_START",
    "E221": "CHOICE_INIT",
    "E222": "CHOICE_SET",
    "E223": "CHOICE_JUMP",
    "E224": "THRUST_FORCE",
    "E225": "B_THRUST_FORCE",
    "E226": "B_THRUST_FORCE_2",
    "E227": "PSY_LOAD",
    "E228": "PSY_BUTTON",
    "E229": "PSY_LABEL_SET",
    "E230": "PSY_LOCK_BREAK",
    "E231": "PSY_CLEAR",
    "E232": "PSY_INDUCTION_START",
    "E233": "PSY_INDUCTION_END",
    "E234": "PSY_END",
    "E235": "PSY_ROCK_SET",
    "E237": "PSY_ROCK_BLACK",
    "E238": "PSY_FORCE_END",
    "E239": "PSY_START_NO_DEMO",
    "E240": "EXAM_MESS_INIT",
    "E241": "EXAM_MESS_SET",
    "E242": "EXAM_MESS_END",
    "E243": "EXAM_START",
    "E244": "EXAM_ANSWER_SET",
    "E245": "EXAM_MESS_NEXT_SET",
    "E246": "PSY_UNLOAD",
    "E247": "PSY_KOKONE_BREAK_SETUP",
    "E248": "B_EXAM_NEXT_FOLLOW",
    "E249": "B_EXAM_FAILD",
    "E250": "PSY_THRUST_ANSWER_SET",
    "E252": "STAFFROLL_TIMER",
    "E253": "STAFFROLL_TIMER_WAIT",
    "E254": "STAFFROLL_2_WAIT",
    "E255": "B_THRUST_FORCE_NO_KURAE",
    "E256": "PSY_KOKONE_BREAK",
    "E257": "PSY_KOKONE_BREAK_WAIT",
    "E258": "PLAYER_SET",
    "E259": "PARTNER_SET",
    "E260": "MSG_EXAM_PARTNER",
    "E261": "PARTNER_OFF",
    "E266": "PARTNER_EXAM_NEXT_SET",
    "E267": "PARTNER_HINT_LABEL_SET",
    "E268": "PARTNER_DAMAGE_COUNT_RESET",
    "E270": "STAFFROLL_OPEN",
    "E271": "STAFFROLL_CLOSE",
    "E272": "STAFFROLL_INIT",
    "E273": "STAFFROLL_END",
    "E274": "STAFFROLL_2_INIT",
    "E275": "STAFFROLL_2_START",
    "E276": "STAFFROLL_2_END",
    "E277": "INV_EVIDENCE_START_TUTORIAL",
    "E279": "GAUGE_PREDAMAGE",
    "E280": "GAUGE_IN",
    "E281": "GAUGE_OUT",
    "E282": "GAUGE_WAIT",
    "E283": "GAUGE_DAMAGE",
    "E284": "B_LIFE_ZERO",
    "E285": "GAME_OVER",
    "E286": "GAUGE_RESET",
    "E287": "RETRY_ITEM_STORE",
    "E288": "GAME_OVER_PANEL_ONLY",
    "E289": "INV_USE_2D_CAMERA",
    "E290": "INV_EVIDENCE_DEMO",
    "E291": "INV_EVIDENCE_FINISH",
    "E292": "INV_EVIDENCE_INIT",
    "E293": "INV_EVIDENCE_START",
    "E294": "TV_WAIT",
    "E295": "TV_PO_INIT",
    "E296": "TV_OPEN",
    "E297": "TV_NEXT",
    "E298": "TV_SET",
    "E299": "TV_CLOSE",
    "E300": "EVENT_SHOW",
    "E301": "EVENT_END",
    "E302": "TEXTCUT_SHOW",
    "E303": "TEXTCUT_END",
    "E304": "EVENT_FADE_SWAP",
    "E305": "EVENT_FADE_WAIT",
    "E306": "PO_INIT",
    "E307": "PO_START",
    "E308": "PO_POINT_CLOSE",
    "E309": "PO_EVENT_CLOSE",
    "E310": "PO_FINISH",
    "E311": "INV_INIT",
    "E312": "INV_CAM_ADD",
    "E313": "INV_LABEL_SET",
    "E315": "INV_DETAIL_CAM",
    "E316": "INV_CAM_WAIT",
    "E317": "INV_CAM_RET",
    "E318": "INV_HIT_SET",
    "E319": "INV_MOT_SET",
    "E320": "INV_MOT_WAIT",
    "E321": "INV_CAM_SET",
    "E322": "INV_COND_ADD",
    "E324": "INV_OPEN",
    "E326": "INV_EVI_FLAG_SET",
    "E327": "B_HIT_EVIDENCE",
    "E329": "BG_USE_COLOR",
    "E330": "aya",
    "E331": "dam",
    "E332": "gek",
    "E333": "hir",
    "E334": "kia",
    "E335": "sho",
    "E336": "dm0",
    "E338": "f",
    "E339": "f2",
    "E340": "fw",
    "E341": "q0",
    "E342": "q1",
    "E343": "q2",
    "E345": "bak",
    "E346": "skn",
    "E354": "PARTNER_HINT_ENABLE",
    #"E360": "",  # Not in PC port, appears before "ICON PAD_X" icon
    #"E361": "",  # Not in PC port, appears before "ICON PAD_L" icon
    #"E362": "",  # Not in PC port, appears before "ICON PAD_R" icon
    #"E363": "",  # Not in PC port, appears before "ICON PAD_CROSS" icon
    #"E364": "",  # Not in PC port, appears before "ICON PAD_SLIDE" icon
    "E369": "DTC_INIT",
    "E370": "DTC_INDEX_INIT",
    "E371": "DTC_MODE",
    "E372": "DTC_INDEX_TALK",
    "E373": "DTC_INDEX_INVEST",
    "E374": "DTC_INDEX_MOVE",
    "E375": "DTC_INDEX_THRUST",
    "E376": "DTC_TALK_FORCE_IN",
    "E377": "DTC_TALK_SET",
    "E378": "DTC_TALK_UPDATE",
    "E379": "DTC_THRUST_INIT",
    "E380": "DTC_THRUST_SET",
    "E381": "B_DTC_THRUST",
    "E382": "DTC_INDEX_INIT_END",
    "E383": "DTC_INV_LABEL",
    "E384": "B_DTC_SETUP",
    "E385": "DTC_TOPIC_INIT",
    "E386": "DTC_MOVE_SET",
    "E388": "DTC_MOVE_FLAG",
    "E390": "DTC_END_INIT",
    "E391": "DTC_END_ITEM_SET",
    "E392": "DTC_END_FLAG_SET",
    "E393": "DTC_START",
    "E394": "B_DTC_END",
    "E397": "INTERVAL",
    "E398": "KOKORO_RANDOM_NOISE_START",
    "E399": "KOKORO_RANDOM_NOISE_END",
    "E400": "KOKORO_INIT",
    "E401": "KOKORO_END",
    "E402": "KOKORO_DEMO",
    "E403": "KOKORO_SET_PHRASE",
    "E404": "KOKORO_UPDATE_EXAM",
    "E405": "KOKORO_UPDATE",
    "E406": "KOKORO_TUTO_NOISE_START",
    "E407": "KOKORO_TUTO_NOISE_END",
    "E409": "KOKORO_SET_CAPTION",
    "E410": "KOKORO_EXAM_TESTIMONY_SET_EX",
    "E411": "KOKORO_UPDATE_DELAY",
    "E412": "KOKORO_WAIT",
    "E413": "KOKORO_EXAM_TESTIMONY_SET",
    "E414": "KOKORO_EXAM_MESS_SET",
    "E416": "B_KOKORO_PHRASE",
    "E417": "KOKORO_SAGURU_ADD_HIT_MASK",
    "E418": "KOKORO_TUKITO_ADD_TESTIMONY_EX",
    "E419": "KOKORO_BGM",
    "E421": "KOKORO_SAGURU_ADD_TESTIMONY",
    "E422": "KOKORO_SAGURU_ADD_PHRASE",
    "E423": "KOKORO_NOISE",
    "E425": "KOKORO_SAGURU",
    "E426": "KOKORO_TUKITO_ADD_TESTIMONY",
    "E427": "KOKORO_TUKITO_ADD_PHRASE",
    "E428": "KOKORO_TUKITO",
    "E429": "KOKORO_TUKITO_TUTO_PHRASE",
    "E430": "KOKORO_TUTO_IN",
    "E431": "KOKORO_TUTO_OUT",
    "E432": "KOKORO_TUTO_SET_ICON",
    "E433": "KOKORO_TUKITO_TUTO_IN",
    "E434": "KOKORO_TUKITO_TUTO_OUT",
    "E435": "KOKORO_CLEAR_TESTIMONY",
    "E436": "KOKORO_SET_CAM",
    "E437": "KOKORO_SHUTDOWN",
    "E438": "KOKORO_SHOW",
    "E439": "KOKORO_HIDE",
    "E440": "EVENT_MOVE",
    "E441": "EVENT_MOVE_WAIT",
    "E442": "EVENT_SHOW_FADE",
    "E443": "EVENT_END_FADE",
    "E444": "EVENT_SHOW_BACK",
    "E445": "MOVIE_PLAY",
    "E446": "MOVIE_WAIT",
    "E449": "MEMO_SET_TASK",
    "E450": "MEMO_ALL_REMOVE",
    "E451": "MEMO_TASK_FINISH",
    "E452": "MEMO_SET_SUMMARY",
    "E453": "EVENT_SHOW_FADE_BACK",
    "E454": "EVENT_END_FADE_BACK",
    "E455": "MEMO_SET_SUMMARY_P2",
    "E456": "KOKORO_TUKITO_ADD_TESTIMONY_FLAG",
    "E457": "BB_SMALL_MSG_WAIT",
    "E458": "BB_SMALL_MSG",
    "E459": "BB_BIG_MSG",
    "E460": "COMBO_THUMB_ON",
    "E461": "COMBO_THUMB_OFF",
    "E462": "COMBO_GET_KEYWORD",
    "E465": "COMBO_START",
    "E466": "COMBO_START_RESUME",
    "E467": "COMBO_END",
    "E468": "COMBO_WAIT",
    "E469": "COMBO_NEXT",
    "E470": "COMBO_EVENT_SHOW",
    "E471": "COMBO_EVENT_END",
    "E474": "COMBO_KEYWORD_BACK",
    "E476": "COMBO_WAIT_KEYWORD",
    "E477": "COMBO_WAIT_EVENT",
    "E478": "COMBO_WAIT_THUMB",
    "E480": "COMBO_FAIL",
    "E481": "COMBO_REBIRTH",
    "E483": "COMBO_WAIT_LINE",
    "E484": "COMBO_BG_SPEED",
    "E485": "COMBO_END_RESUME",
    "E486": "COMBO_STAR_LEVEL",
    "E487": "COMBO_THUMB_ON_LINE",
    "E488": "KOKORO_TUKITO_ADD_TESTIMONY_READ",
    "E489": "MOVIE_PLAY_EX",
    "E511": "COMBO_FAIL_IF",
    "E512": "DTC_MOVE_FLAG_SET",
    "E513": "MOVIE_PLAY_LIMIT",
    "E514": "BGM_PREPARE_PAUSE",
    "E515": "BGM_PREPARE_RESUME",
    "E750": "PRE_SET_SCENE",
    "E751": "PRE_SET_ITEM_ADD",
    "E752": "PRE_SET_ITEM_REMOVE",
    "E753": "PRE_SET_ITEM_REMOVE_ALL",
    "E754": "PRE_SET_FLAG_ON",
    "E755": "PRE_SET_FLAG_OFF",
    "E756": "PRE_SET_ITEM_UPDATE",
    "E761": "PRE_SET_DTC_TOPIC_ON",
    "E762": "PRE_SET_DTC_MOVE_FLAG",
    "E765": "PRE_SET_NOW_DATA_SET",
    "E766": "PRE_SET_MEMO_SET_TASK",
    "E767": "PRE_SET_MEMO_ALL_REMOVE",
    "E768": "PRE_SET_MEMO_TASK_FINISH",
    "E769": "PRE_SET_MEMO_SET_SUMMARY",
    "E770": "PRE_SET_MEMO_SET_SUMMARY_P2",
    "E800": "ROWE"
}

# Define the mappings for GS6 - PW: AA - Spirit of Justice (SoJ)
# (These ones first only appear in SoJ)
soj_mapping = {
    "ICON PAD_Y": "ICN 21",
    "ICON PAD_A": "ICN 22",
    "ICON PAD_B": "ICN 23",
    "E010": "c5",
    "E039": "SCENE_JUMP_NEXT",
    "E063": "WND_CLOSE",
    "E067": "DEMO_UNK1", # only in demo, perhaps DEMO_FILTER?
    "E096": "stse_mwn",
    "E171": "GADGET_WAIT",
    "E182": "MNK_DURUKU_FAILD_LABEL",
    "E219": "INV_EVI_RET",
    "E262": "HAMMER_PLAY_STOP_SOUND",
    "E263": "NOT_GUILTY_CIVIL",
    "E328": "INV_USE_LUMI",
    "E347": "qa",
    "E353": "skn0",
    "E356": "QUAKE",
    #"E357": "",  # Not in PC port, appears before "ICON PAD_A" icon
    #"E358": "",  # Not in PC port, appears before "ICON PAD_B" icon
    #"E359": "",  # Not in PC port, appears before "ICON PAD_Y" icon
    "E365": "DTC_MODE_NO_BTN_SELECT",
    "E366": "DTC_MODE_NO_INV",
    "E367": "INV_CAM_SET2",
    "E368": "DTC_MODE_NO_MOVE",
    "E463": "COMBO_LOAD",
    "E464": "COMBO_OUT_PLAYER",
    "E472": "COMBO_EVENT_THUMB_END",
    "E473": "COMBO_SET_WAY",
    "E475": "COMBO_REBIRTH_SE",
    "E482": "COMBO_THUMB_CLR",
    "E490": "DTC_TOPIC_FLAG_OFF",
    "E491": "INV_CAM_SET_END",
    "E492": "INV_POINT_RESET",
    "E493": "INV_EVI_THRUST_START_TUTO",
    "E494": "CHR_SET_MULTI",
    "E495": "CHR_SET_MULTI_NOSTART",
    "E496": "CHR_SET_SOUHEI",
    "E516": "KS_ARC_LOAD",
    "E517": "KS_ARC_RELEASE",
    "E518": "KS_BGM",
    "E519": "KS_SETUP_PHASE",
    "E520": "KS_EXECUTE",
    "E521": "KS_SET_BRANCH",
    "E522": "MEMO_SET_SUMMARY_CIVIL",
    "E523": "ANIME_PLAY",
    "E524": "CAM_PLAY_DTC_BG_FADE_DISABLE",
    "E526": "CAM_PLAY",
    "E527": "CAM_SW",
    "E528": "SPIRIT_SETUP",
    "E529": "SPIRIT_EXECUTE",
    "E530": "SPIRIT_SET_PHASE",
    "E531": "SPIRIT_FINAL",
    "E532": "SPIRIT_IS_DECIDE",
    "E533": "SPIRIT_SENSE_CHECK",
    "E535": "SPIRIT_REQ_AST_CHG",
    "E536": "SPIRIT_REQ_AST_INS",
    "E537": "SPIRIT_AST_CHG_EXE",
    "E539": "ASSERTION_START",
    "E541": "KS_SETUP_BERSERK_2ND",
    "E543": "SPIRIT_ANSWER_JUMP",
    "E545": "SPIRIT_START_DEMO",
    "E547": "SPIRIT_DANCE_DEMO",
    "E548": "SPIRIT_STATIC_IMAGE_IN",
    "E549": "SPIRIT_STATIC_IMAGE_OUT",
    "E550": "SPIRIT_TUTORIAL",
    "E553": "CAM_ZOOM_IN_POS",
    "E556": "FINGER_INIT",
    "E557": "FINGER_START",
    "E558": "FINGER_LABEL_SET",
    "E559": "FINGER_SET_OFFSET",
    "E560": "FINGER_TUTO",
    "E561": "FINGER_COLLATE",
    "E562": "POM_SETUP",
    "E563": "POM_EXECUTE",
    "E564": "POM_FINAL",
    "E565": "POM_REG_ANSWER",
    "E566": "POM_CLEAR_ANSWER",
    "E567": "POM_B_CORRECT",
    "E568": "POM_B_HIT_ID",
    "E570": "BOX_SETUP",
    "E571": "BOX_EXECUTE",
    "E572": "BOX_FINAL",
    "E573": "BOX_B_SUCCESS",
    "E574": "BOX_B_FAILURE",
    "E575": "BOX_OPEN",
    "E576": "CAM_ZOOM_IN_OFFS",
    "E579": "INV_EVI_THRUST_START",
    "E580": "INV_EVI_MOT_PLAY",
    "E581": "INV_EVI_COLLISION",
    "E582": "INV_EVI_MOT_SET",
    "E583": "FINGER_ARROW",
    "E585": "DELTA_TIME_SET",
    "E587": "SPIRIT_B_FAIL_TYPE",
    "E588": "CHR_TAG_WAIT",
    "E589": "SDL_EV_ID_WAIT",
    "E590": "EFC_LINE_SET",
    "E591": "EFC_LINE_END",
    "E592": "SPIRIT_CHANGE_EXIT",
    "E595": "NOT_GUILTY_ANIM",
    "E596": "DEMO_UNK2", # only in demo, some sort of set or load thing?
    "E597": "DEMO_UNK3", # only in demo, some sort of set or load thing?
    "E598": "CAM_ZOOM_REVERSE",
    "E599": "CAM_PLAY_LOOK_UP",
    "E609": "BGM_PLAY_VOLUME",
    "E611": "BGM_VOLUME_OF",
    "E612": "STRM_PLAY",
    "E613": "STRM_STOP",
    "E614": "STRM_FADE_IN",
    "E615": "STRM_FADE_OUT",
    "E616": "STRM_WAIT_OF",
    "E617": "STRM_WAIT",
    "E619": "STRM_VOLUME_OF",
    "E620": "STRM_PLAY_NC",
    "E621": "STRM_FADE_OUT_OF",
    "E638": "dog_se",
    "E641": "SE_CAM_VOL_MIN_SET",
    "E642": "SE_CAM_FO_FORCE",
    "E643": "DEMO_UNK4", # only in demo, some sorta SE_DEMO_...?
    "E646": "SE_FADE_OUT_WAIT",
    "E661": "RELIC_DEMO_FINAL",
    "E662": "SCE00_OP_DEMO",
    "E663": "SCE00_OP_DEMO_WAIT",
    "E664": "KS_TUTORIAL",
    "E665": "KS_SET_THROUGH",
    "E675": "RESET_LAYOUT_CAM",
    "E676": "WALLPAPER_SET",
    #"E677": "INSIGHT_MODE",  # Not in PC port, only seems used in the spirit insight as a boolean
    "E678": "PHOTO_FACE_SET",
    "E732": "DEMO_UNK5", # only in demo, DEMO_END?
    "E735": "DEMO_UNK6", # only in demo
    "E771": "PRE_SET_PLAYER_SET",
    "E772": "PRE_SET_SCENARIO_MODE",
    "E773": "PRE_SET_MEMO_SET_SUMMARY_CIVIL",
    "E795": "MSGS",
    "E796": "MSGE"
}

# Include certain command names here that differ in SoJ, but use the same event number as in DD
soj_overwrite_mapping = {
    # Commands that have been separated are below, because their name matches in both games
    "E525": "CAM_WAIT",
    "E600": "BGM_CONTEXT",
    "E601": "BGM_WAIT",
    "E602": "BGM_SWAP",
    "E603": "BGM_FADE_OUT_OF",
    "E604": "BGM_PLAY",
    "E605": "BGM_STOP",
    "E606": "BGM_FADE_IN",
    "E607": "BGM_FADE_OUT",
    "E608": "BGM_VOLUME",
    "E610": "BGM_WAIT_OF",
    "E630": "SE_PLAY",
    "E631": "SE_STOP",
    "E632": "SE_VOLUME",
    "E633": "SE_WAIT",
    "E634": "SE_FADE_IN",
    "E635": "SE_FADE_OUT",
    "E639": "SE_VOLUME_OF",
    # Commands that use same event numbers are below (these ones need the new names)
    "E081": "bgm_mw",
    "E082": "BOKEH_FILTER_ON",
    "E083": "BOKEH_FILTER_OFF",
    "E084": "BOKEH_FILTER_WAIT",
    "E085": "stse_mw",
    "E086": "WND_OPEN_QUICK",
    "E087": "WND_CLOSE_QUICK",
    "E088": "FADE_SCENE",
    "E090": "FADE_KAISOU_START_IN",
    "E091": "FADE_KAISOU_NOCAM_START",
    "E093": "FADE_KAISOU_END_IN",
    "E094": "FADE_KAISOU_NOCAM_END",
    "E097": "FADE_KAISOU_EVENT_START",
    "E098": "FADE_KAISOU_EVENT_END",
    "E114": "INV_REGION_SET",
    "E122": "BG_ORNAMENT_MTR_ANM",
    "E127": "BOW",
    "E129": "BG_ORNAMENT_ALPHA",
    "E130": "SET_CAM_FAR",
    "E142": "CHR_SET_AND_REMOVAL",
    "E143": "CHR_WAIT_LINK",
    "E148": "CHR_ANIME_NSS",
    "E149": "CHR_SET_NOSTART",
    "E150": "CHR_FORCE_MOUTH",
    "E159": "CHR_LOOP_WAIT",
    "E162": "CHR_LEAVE",
    "E163": "CHR_ANIME_NO_SE",
    "E193": "MARK",
    "E194": "CHR_SET_VOFF",
    "E259": "PO_ANSWER_SET",
    "E261": "DEMO_DEL",
    "E268": "INV_CAM_RET_FORCE",
    "E515": "CAM_RETURN_DEFAULT"
}

# Define tags that shouldn't have the "XXXX " prefix
# Note: ICN = ICON (e.g. control buttons)
no_prefix_tags = {
    "CENTER",
    "ICN",
    "PAGE"
}

# Do not separate with commas, but keep these with a space
no_comma_tags = {
    "ICN ",
    "ICN 0",
    "ICN 2",
    "ICN 4",
    "ICN 5",
    "ICN 6",
    "ICN 7",
    "ICN 8",
    "ICN 9",
    "ICN 10",
    "ICN 11",
    "ICN 12",
    "ICN 13",
    "ICN 14",
    "ICN 15",
    "ICN 16",
    "ICN 19",
    "ICN 20",
    "ICN 21",
    "ICN 22",
    "ICN 23"
}

# Define tags that shouldn't be included
# (there may be others not in the PC port, these are the ones that caught my attention)
remove_tags = {
    "SEC_END" # from the GMD script conversion, used as a separator tag
    #"E042",    # not in PC port, appears before "CNTR" (CENTER)
    #"E357",    # Not in PC port, appears before "ICON PAD_A" icon
    #"E358",    # Not in PC port, appears before "ICON PAD_B" icon
    #"E359",    # Not in PC port, appears before "ICON PAD_Y" icon
    #"E360",    # Not in PC port, appears before "ICON PAD_X" icon
    #"E361",    # Not in PC port, appears before "ICON PAD_L" icon
    #"E362",    # Not in PC port, appears before "ICON PAD_R" icon
    #"E363",    # Not in PC port, appears before "ICON PAD_CROSS" icon
    #"E364",    # Not in PC port, appears before "ICON PAD_SLIDE" icon
    #"E677",    # Not in PC port, appears at spirit insight (SoJ)
    #"MCRE",    # not in PC port
    #"MCRS"     # not in PC port
}

# For the PC option, the 3DS tags are not needed
remove_tags_pc = {
    "SEC_END", # from the GMD script conversion, used as a separator tag
    "E042",    # not in PC port, appears before "CNTR" (CENTER)
    "E357",    # Not in PC port, appears before "ICON PAD_A" icon
    "E358",    # Not in PC port, appears before "ICON PAD_B" icon
    "E359",    # Not in PC port, appears before "ICON PAD_Y" icon
    "E360",    # Not in PC port, appears before "ICON PAD_X" icon
    "E361",    # Not in PC port, appears before "ICON PAD_L" icon
    "E362",    # Not in PC port, appears before "ICON PAD_R" icon
    "E363",    # Not in PC port, appears before "ICON PAD_CROSS" icon
    "E364",    # Not in PC port, appears before "ICON PAD_SLIDE" icon
    "E677",    # Not in PC port, appears at spirit insight (SoJ)
    "MCRE",    # not in PC port
    "MCRS"     # not in PC port
}

# Assemble the main mapping dictionary
aa56_mapping = {**dd_mapping, **soj_mapping}
reverse_mapping = {v: k for k, v in aa56_mapping.items()}
aa56_mapping2 = {**dd_mapping, **soj_mapping, **soj_overwrite_mapping}
reverse_mapping2 = {v: k for k, v in aa56_mapping2.items()}

# Precompile regex patterns
TAG_PATTERN = re.compile(r"\{(.*?)\}")
LABEL_TEST_PATTERN = re.compile(r"\{(\d+:\d+.*?)\}")
LABEL_PATTERN = re.compile(r"[^:}]+(?=})")
REMOVE_TAGS_PATTERNS = [re.compile(f"<{tag}[^>]*>") for tag in remove_tags]
REMOVE_TAGS_PC_PATTERNS = [re.compile(f"<{tag}[^>]*>") for tag in remove_tags_pc]

# Precompile mappings for efficiency
aa56_mapping_replacements = [(re.compile(f"<{re.escape(entry)}"), f"<{code}") for entry, code in aa56_mapping.items()]
reverse_mapping_patterns = [(re.compile(rf"<{re.escape(code)}(?=[, >])"), f"<{entry}") for code, entry in reverse_mapping.items()]
aa56_mapping_replacements2 = [(re.compile(f"<{re.escape(entry)}"), f"<{code}") for entry, code in aa56_mapping2.items()]
reverse_mapping_patterns2 = [(re.compile(rf"<{re.escape(code)}(?=[, >])"), f"<{entry}") for code, entry in reverse_mapping2.items()]


# Function to convert structured text to JSON format
def convert_to_json(input_text, isGMD=True, isSOJ=False):
    """Converts structured text into JSON format."""
    result = {}
    lines = input_text.strip().splitlines()
    match = TAG_PATTERN.search(lines[0])
    result["name"] = match.group(1) if match else "Unknown"

    labels = []
    current_label, current_data = None, []

    for line in lines[1:]:
        if line.startswith("{") and line.endswith("}"):
            if isGMD:
                test_line = LABEL_TEST_PATTERN.search(line)
                if test_line:
                    if current_label:
                        labels.append([current_label, "".join(current_data).strip("\r\n")])
                    current_label = LABEL_PATTERN.search(line).group(0)
                    current_data = []
            else:
                if current_label:
                    labels.append([current_label[1:], "".join(current_data).strip("\r\n")])
                current_label = LABEL_PATTERN.search(line).group(0)
                current_data = []
        else:
            if isSOJ:
                for pattern, replacement in aa56_mapping_replacements2:
                    line = pattern.sub(replacement, line)
            else:
                for pattern, replacement in aa56_mapping_replacements:
                    line = pattern.sub(replacement, line)

            for pattern in REMOVE_TAGS_PATTERNS:
                line = pattern.sub("", line)

            line = re.sub(r"<([^>]+)>", 
                          lambda m: f"<{m.group(1).replace(' ', ',')}>" if m.group(1) not in no_comma_tags else m.group(0),
                          line)

            line = re.sub(r"<(?!XXXX\s)(\w+)([ ,>])", 
                          lambda m: f"<XXXX {m.group(1)}{m.group(2)}" if m.group(1) not in no_prefix_tags else m.group(0),
                          line)
            
            current_data.append(line + "\r\n")

    if current_label:
        if isGMD:
            labels.append([current_label, "".join(current_data).strip("\r\n")])
        else:
            labels.append([current_label[1:], "".join(current_data).strip("\r\n")])

    result["labels"] = labels
    return json.dumps(result, indent=2, ensure_ascii=False)


# Function to convert JSON back to structured text format
def json_to_text(json_data, isGMD=True, isSOJ=False, isTagsKeep=False):
    """Converts JSON format back to structured text."""
    result = f"{{{json_data['name']}}}\n\n"

    for label_data in json_data['labels']:
        result += f"{{{label_data[0]}}}\n"
        commands = label_data[1].replace('\r\n', '\n')

        # Restore original tag names from XXXX
        commands = re.sub(r"<XXXX\s(\w+)([ ,>])", 
                          lambda m: f"<{m.group(1)}{m.group(2)}" if m.group(1) not in no_prefix_tags else m.group(0),
                          commands)

        # Remove deprecated tags
        if isGMD:
            for pattern in REMOVE_TAGS_PATTERNS:
                commands = pattern.sub("", commands)
        else:
            if not isTagsKeep:
                for pattern in REMOVE_TAGS_PC_PATTERNS:
                    commands = pattern.sub("", commands)

        # Apply dictionary-based replacements
        if isGMD and isSOJ:
            for pattern, replacement in reverse_mapping_patterns2:
                commands = pattern.sub(replacement, commands)
        elif isGMD and not isSOJ:
            for pattern, replacement in reverse_mapping_patterns:
                commands = pattern.sub(replacement, commands)

        # Replace commas with spaces inside angle brackets
        commands = re.sub(r"<([^,>]+(?:,[^,>]+)*)>", lambda m: f"<{m.group(1).replace(',', ' ')}>", commands)

        # Section end
        if isGMD:
            result += f"{commands}<SEC_END>\n\n"
        else:
            result += f"{commands}\n\n"

    return result.strip()


# Function to process each file (for multiprocessing)
def process_file(file, args):
    encoding = 'utf-8'
    buffering = 8192
    base_name, ext = os.path.splitext(file)
    output_file = args.output if args.output and len(args.input_files) == 1 else (
        f"{base_name}.json" if args.json else f"{base_name}.txt"
    )
    # Set flags based on arguments
    isGMD = not args.pc
    isSOJ = args.soj
    isTagsKeep = args.keeptags

    with open(file, "r", encoding=encoding, buffering=buffering) as infile:
        input_data = infile.read()

    # Perform conversion
    output_data = (
        convert_to_json(input_data, isGMD=isGMD, isSOJ=isSOJ) 
        if args.json 
        else json_to_text(json.loads(input_data), isGMD=isGMD, isSOJ=isSOJ, isTagsKeep=isTagsKeep)
    )

    with open(output_file, "w", encoding=encoding, buffering=buffering) as outfile:
        outfile.write(output_data)

    print(f"Processed: {file} -> {output_file}") 


# Parse command-line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="For GS5 and GS6: Convert structured GMD/gs456scr text to JSON or vice versa.")
    parser.add_argument("input_files", help="Path to the input file(s)", nargs='+')
    parser.add_argument("-j", "--json", action="store_true", help="Convert text to JSON")
    parser.add_argument("-t", "--txt", action="store_true", help="Convert JSON to text")
    parser.add_argument("-s", "--soj", action="store_true", help="Use this for SoJ (GS6) files to fix/get all its proper command names")
    parser.add_argument("-p", "--pc", action="store_true", help="Use to convert (for) the PC port's files")
    parser.add_argument("-k", "--keeptags", action="store_true", help="Use this to keep any tags that would be removed with -p")
    parser.add_argument("-o", "--output", help="Output file (only for single files)")
    return parser.parse_args()


# Main function with multiprocessing
def main():
    args = parse_arguments()

    # Expand file patterns
    input_files = [file for pattern in args.input_files for file in glob.glob(pattern)]

    if not input_files:
        print("No files found!")
        return

    # Process files in parallel
    with ProcessPoolExecutor() as executor:
        executor.map(process_file, input_files, [args] * len(input_files))


if __name__ == "__main__":
    main()
