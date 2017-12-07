# Trimm-CLI
Built on Python using click and requests

### Setup
```
pip install click
pip install requests
pip install tqdm
``` 

### Usage
To install a bundle:
```
python trimm.py install <bundlename>
``` 
To update your bundles from your trimm.json, run:
```
python trimm.py update
``` 
To pull all missing bundles from your trimm.json, run:
```
python trimm.py pull
``` 
To create zips for all missing bundles, run:
```
python trimm.py make_zips
``` 
To see all line command args run:
```
python trimm.py --help
``` 