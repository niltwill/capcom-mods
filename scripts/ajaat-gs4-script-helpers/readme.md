Using the GS4 converter script, I noticed that it does have the inconvenience that you need to use special unicode characters for non-ASCII chars, like [U+00E4] for "ä". This spells trouble for languages that are not English. If you replace more than a few sentences or words, this can quickly become unmanageable or extremely tedious.

So I made a few helper scripts that may ease this process.

* **unicode-to-utf8.py**

Use this to convert the decoded text file of the script, so that you get proper unicode characters, and don't have to bother with stuff like `[U+00AC]`.
This will immensely help in readability of the text, especially if your language consists (only or mainly) of non-Latin characters.

Example: `unicode-to-utf8.py sc0_0_h03.user.2.de.txt sc0_0_h03.user.2.de-converted.txt`

* **convert-unicode-text.py**

You can put your sentences/words into this as an argument, to convert them back to the required format.

Example: `convert-unicode-text.py "mädchen"`
(Output: `m[U+00E4]dchen`)

* **convert-unicode-file.py**

Same thing as the earlier script, but this takes an input file and produces an output file. With a translation project, if you collected all the sentences into a separate file, then you can use this to convert all that back in one go.

Example: `convert-unicode-file.py test1.txt test1-o.txt`

A really short bit that I collected, only for demonstration:

```
-- Das letzte Blatt --
Letztes Blatt...
Männer\57345|beide hatten "Full House".
!Es geben jede Karte viermal\57345|in Kartenspiel, von Ass\57345|bis König.
Wenn Sie ansehen Blatt von\57345|Männer,\57356|\12| man kann sehen Betrug!\57346|\57489|'Plötzlich aus Spiel werden\57345|Streit, dah!\57356|\15| Trick von\57345|Angeklagter entdeckt!
```

Becomes:

```
-- Das letzte Blatt --
Letztes Blatt...
M[U+00E4]nner\57345|beide hatten "Full House".
!Es geben jede Karte viermal\57345|in Kartenspiel, von Ass\57345|bis K[U+00F6]nig.
Wenn Sie ansehen Blatt von\57345|M[U+00E4]nner,\57356|\12| man kann sehen Betrug!\57346|\57489|'Pl[U+00F6]tzlich aus Spiel werden\57345|Streit, dah!\57356|\15| Trick von\57345|Angeklagter entdeckt!
```

Which then can be put back to where it needs to go in the decoded text file. You still need to be able to find the location of these texts. And remember, that you need to keep non-language related unicode characters unchanged.