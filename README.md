Stohrer-Sax-Pad-SVG-Generator
Generates SVGs for laser cutting saxophone felts, cards, and leathers. Current version is 1.2.

Features: SVG creation, basic nesting, layout in proscribed space (unless it won't fit), save/delete pad presets, center hole options (none, 3.0mm, 3.5mm), select inches-cm-mm for sheet size, advanced options to change sizing rules.  

Update 1.2 is refactored using Gemini, and adds the options menu as well as save-on-exit for sheet size and center hole selection.  


Should work with default settings for leather between .011"- .014", and sizing of leather disc assumes a .125" thick felt with cardstock between .010 and .025 being acceptable for overwrap, providing for a final pad thickness of .160" to .175" or so.

You will need to apply your own feeds/speeds and kerf settings depending on your cutter in Lightburn. SVGs may not present correctly in other apps (especially default image viewers). 

Make sure to enter the pad sizes like it suggests, e.g. "34.0 x 10" without the quotes, and each size on a different line.  If you use a comma rather than a decimal point, the value will be ignored.  

Windows is the intended OS for using this program.  Click on "releases" and download the exe. 

If you wish to run this in linux with python3, you must also install python3-svgwrite and python3-tk, but I can provide no technical support.

Put the .exe in a folder. Your presets and preferences will be saved in json files in that folder.

I have no idea how to code, this was made with chatbots. Hope it works for you!

-Matt
