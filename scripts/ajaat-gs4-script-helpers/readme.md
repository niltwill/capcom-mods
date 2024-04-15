Using the GS4 converter script, I noticed that it does have the inconvenience that you need to use special decimal characters for non-ASCII chars, like `\L228` for "ä". This spells trouble for languages that are not English. If you replace more than a few sentences or words, this can quickly become unmanageable or extremely tedious. So I made a few helper scripts that may ease this process.

First use the `decimal-to-unicode` converter, either the file or the folder script.
Then edit what you need, and once you're finished, use `unicode-to-decimal` to convert it back.
Finally, re-encode the text file(s).
