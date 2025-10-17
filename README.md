Stohrer-Sax-Pad-SVG-Generator
Generates SVGs for laser cutting saxophone felts, cards, and leathers. Current version is 1.375.


Features: SVG creation, basic nesting, layout in proscribed space (unless it won't fit), save/delete pad presets, center hole options (none, 3.0mm, 3.5mm, custom), user-defined minimum pad size for center hole, select inches-cm-mm for sheet size, advanced options to change sizing rules, custom rules for size engraving on materials.  

Update 1.375 corrected a few minor gui bugs and adds MacOS version.  


Should work with default settings for leather between .011"- .014", and sizing of leather disc assumes a .125" thick felt with cardstock between .010 and .025 being acceptable for overwrap, providing for a final pad thickness of .160" to .175" or so.

You will need to apply your own feeds/speeds and kerf settings depending on your cutter in Lightburn. SVGs may not present correctly in other apps (especially default image viewers). 

Make sure to enter the pad sizes like it suggests, e.g. "34.0 x 10" without the quotes, and each size on a different line.  If you use a comma rather than a decimal point, the value will be ignored.  

Windows is the intented OS, and there is no Mac version.

If you wish to run this in linux with python3, you must also install python3-svgwrite and python3-tk, but I can provide no technical support.

For Windows, put the .exe in a folder. Your presets and preferences will be saved in json files in that folder.  If you are upgrading from a previous version, simply replace the .exe and leave the .jsons and your old settings and presets will carry over.  

For Windows you get a warming against running "unsigned" programs since I am not going to pay a fee to be a "developer" to make that go away.  Only happens on first run.  

I have no idea how to code, this was made with chatbots. Hope it works for you!

-Matt
