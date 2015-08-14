hmththvtro.html: data hmththvtro.thml process.py env
	env/bin/python process.py data > $@

.PHONY: clean
clean:
	rm -f hmththvtro.html cache/

.PHONY: data
data: env
	bash get_data.sh cache/
	env/bin/python yaml2json.py 

env:
	virtualenv env/
	pip install -r requirements.txt
