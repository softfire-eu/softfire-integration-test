#!/bin/bash

INNER_CSAR_FILE="nsd.csar"
INNER_CSAR_FOLDER"Files/"


function foo {
[ -d _tar ] || ( echo "_tar folder does not exist! exit..."; exit 0 )

find . -maxdepth 2 -name vnfd.json |
	while read line
	do
		NFNAME=$(dirname $line)
		echo $NFNAME
		tar -c --hard-dereference --dereference -f _tar/${NFNAME}.tar -C $NFNAME vnfd.json Metadata.yaml scripts
	done
}

function do_connectivitytest {

	#tar -c --hard-dereference --dereference -f _tar/${NFNAME}.tar -C $NFNAME vnfd.json Metadata.yaml scripts
	pushd connectivitytest
	pushd Files
	zip -r nsd.csar . -x ".*" -x "*/.*"
	popd
	zip ../connectivitytest.csar Files/nsd.csar Definitions/experiment.yaml TOSCA-Metadata/TOSCA.meta TOSCA-Metadata/Metadata.yaml
	popd
	rm connectivitytest/Files/nsd.csar
}

do_connectivitytest