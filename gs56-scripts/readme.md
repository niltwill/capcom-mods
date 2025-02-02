# gs56-gmd-converter.py

This script can be used to convert the GMD (script-related) files from the Nintendo 3DS port for GS5 and GS6 (Dual Destinies and Spirit of Justice) to editable text files and also convert them back to GMD. This Python script be can easily changed to suit other GMD files for different games, with slight adjustments depending on how the header is constructed. There's also support for big-endian with `--be` (default is little-endian), although I did not test that.

### Usage

Here are some examples, 'd' for decode, 'e' for encode:

```
python gs56-gmd-converter.py d GS6_GMD\*.gmd
python gs56-gmd-converter.py e GS6_GMD\*.txt

python gs56-gmd-converter.py d GS5_GMD\*.gmd
python gs56-gmd-converter.py e --xor GS5_GMD\*.txt
```

Note that `--xor` is used to encrypt the content back, which is only needed for Dual Destinies (DD). By default this is not enabled.

To get the raw data that is not very formatted:

```
python gs56-gmd-converter.py i --out GS6_GMD\*.gmd
python gs56-gmd-converter.py i --out GS5_GMD\*.gmd
```

### Labels

You can also experiment with the labels... But I recommend not to delete or add new labels. Best to change only the text sections within the labels. As for editing the label names: it's better not to edit these either. If you want to try, I can explain my assumption as to how to do it. PW:AA - SoJ (GS6) may take this more dynamically regarding the labels, so the following info may only apply for PW:AA - DD (GS5): While the label names can be edited, and they can be longer or shorter, but you have to make sure that the first and last pointer offset remains unchanged. This means do not edit the first and last label. For others, you have to change the pointer offsets manually to accomodate the new size.

For example, from `_sce00_c000_0000_eng` (DD):

> {0:688390896:LABEL_0000}\
> {1:688390907:L_OPEND}\
> {2:688390915:L_OPEND_sub}

If you change it like this (shorten "L_OPEND" to "L_OP"):

> {0:688390896:LABEL_0000}\
> {1:688390907:L_OP}\
> {2:688390915:L_OPEND_sub}

 Then also change the pointers, where applicable:

> {0:688390896:LABEL_0000} <- unchanged pointer\
> {1:688390907:L_OP} <- unchanged again, because we did not edit "LABEL_0000" (size: 10 + 1, 907 - 896 = 11)\
> {2:688390912:L_OPEND_sub} <- shorter pointer (size of "L_OP" is 4 + 1 = 5, 907 + 5 = 912)

---

# gs56-script-converter.py

This script can be used to to convert the structured text (script) files to JSON files and back, which is what [gs456scr](https://gist.github.com/osyu/5bb86d49153edef5415a7aba09a48ca1) needs to convert it back for the PC port. So this script can handle both the PC port's files with *gs456scr* or the GMD text files you got with the other script.

### Usage

**1.** Convert the GMD text files you got from my other script (GMD -> txt) via the command:

*A. SoJ*: `python gs56-script-converter.py -j -s SoJ_Text\*.txt`\
*B. DD*: `python gs56-script-converter.py -j DD_Text\*.txt`

This converts the files to JSON.

*Warning:* doing this means you lose all GMD data for their recreation, specifically the GMD header and the label info. What you get from this can only be reused for the PC port. For the 3DS, you would need to manually reapply all the missing GMD data, if you want to convert it back to TXT from JSON later. Just be aware of this.

**2.** If the JSON is cumbersome to edit, you can convert them to txt:

*A. SoJ*: `python gs56-script-converter.py -t -s -p -k SoJ_JSON\*.json`\
*B. DD*: `python gs56-script-converter.py -t -p -k DD_JSON\*.json`

Use `-p` to keep the command names, and `-k` to keep the 3DS tags (which would be otherwise removed for the PC port). Also, make sure to always use `-s` if you handle files related to SoJ, due to how it has different command names at the same event numbers as DD. If you do not use that flag, you will not get the correct command names.

**3.** If you want to reuse these txt files for PC port's JSON (with *gs456scr*):

*A. SoJ*: `python gs56-script-converter.py -j -s -p SoJ_JSON\*.txt`\
*B. DD*: `python gs56-script-converter.py -j -p DD_JSON\*.txt`

### Remarks

The icons were remapped according to the PC port's ICN numbers (for the control scheme), but this may not be correct. Edit that as needed. From what I saw when comparing the 3DS and the PC port's script files, you should not reuse them 1-to-1, but only with careful editing and merging. For example, the 3DS port does not actually close the opened `<CENTER>` tags, which may cause text formatting issues. You would need to remedy this manually according to the PC port's scripts. There are also a couple of tags that only seem to appear in the 3DS version, and re-using these in the PC port may not be wise (and vice versa). Besides that, you can observe missing commands that exist in the PC version, but not in the 3DS port.

I will list all of these below:

#### GS6 (SoJ) - commands not in the 3DS scripts:
```
ACHIEVEMENT
ACT_JUMP
ACT_RETURN
B_INV_COND
CHR_ALPHA
COURT_BUSTUP_CAMERA
DISPLAY_BUTTONS_AFTER_FINGER
FINGER_CLOSE
FULLSCREEN_GAME_IOS
HIDE_BUTTONS_BEFORE_FINGER
INV_EVIDENCE_DEMO
RESET_ANTIALIAS
SCREEN_FRAME_IOS
SET_CAM_NEAR
SUB_TUTO_BLACK
SYSTEM_PANEL_IOS
TELOP
```

#### GS5 (DD) - commands not in the 3DS scripts:
```
ACHIEVEMENT
ACT_JUMP
ACT_RETURN
B_CAMERA
B_ENGLISH
B_MOBILE
B_MYSTERY_ONDEVICE
B_TRIAL_DL
B_TRIAL_NW
BGM_PLAY_VOLUME
c5
CHR_FORCE_MOUSE_SE
CHR_SET_2D_OR_3D_NOSTART
dam0
FADE_EVCUT
FADE_EVCUT_WAIT
FULLSCREEN_GAME_IOS
INTERVAL_OPEN
INTERVAL_OPEN_WAIT
INV_EVI_RET
INV_SET_CHR
INV_USE_LUMI
kia0
KOKORO_SAGURU_ADD_TESTIMONY_EX
MYSTERY_INV_INIT
MYSTERY_INV_LABEL_SET
MYSTERY_INV_OPEN
MYSTERY_PLAYER_SET
MYSTERY_RETURN_MENU
MYSTERY_SAVE
OP_DEMO_TITLE
PSY_PO_ANSWER_SET
PSY_ROCK_ICON_ONLY
SCREEN_FRAME_CHANGE_MSG_IOS
SCREEN_FRAME_IOS
SE_LOAD
SE_UNLOAD
sho0
SYSTEM_PANEL_IOS
TGS_TRIAL_END
TRIAL_AUTO_RESET
TRIAL_END
```
