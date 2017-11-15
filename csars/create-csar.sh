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
	zip -r nsd.csar . -x ".*" -x "*/.*" -x "scripts/common"
	popd
	zip ../connectivitytest.csar Files/nsd.csar Definitions/experiment.yaml TOSCA-Metadata/TOSCA.meta TOSCA-Metadata/Metadata.yaml
	popd
	rm connectivitytest/Files/nsd.csar
}

## this function will create links from the common scripipts folder to the machine tpe specifit folders
function create_links_nsd {
	pushd Files/scripts
	for d in adsvm ericssonvm fokusdevvm fokusvm surreyvm; do
		echo "## creating links for $d"
		for f in common/*; do
			FILENAME=$(basename $f)
			if [ "${FILENAME}" != "${d}_connect.sh" ]; then
				echo ln -f -s ../$f ${d}/${FILENAME}
			else
				echo "## skipping $FILENAME for $d"
			fi
		done
	done
	popd
}

do_connectivitytest