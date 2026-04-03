build-SummarizeFunction:
	cp -r src/handler/* "$(ARTIFACTS_DIR)/"
	cp config.yaml "$(ARTIFACTS_DIR)/"
	python -m pip install -r src/handler/requirements.txt -t "$(ARTIFACTS_DIR)/"
