hmththvtro.html: data hmththvtro.thml process.py requirements
	env/bin/python process.py data > $@

.PHONY: clean
clean:
	rm -f hmththvtro.html cache/

.PHONY: data
data: requirements
	bash get_data.sh cache/
	env/bin/python yaml2json.py cache/legislators-current.yaml cache/legislators-current.json
	env/bin/python yaml2json.py cache/legislators-historical.yaml cache/legislators-historical.json

env:
	virtualenv env/

.PHONY: requirements
requirements: env
	env/bin/pip install -r requirements.txt
