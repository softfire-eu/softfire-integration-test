#!/bin/bash

INNER_CSAR_FILE="nsd.csar"
INNER_CSAR_FOLDER"Files/"

function do_connectivitytest {

	#tar -c --hard-dereference --dereference -f _tar/${NFNAME}.tar -C $NFNAME vnfd.json Metadata.yaml scripts
	pushd connectivitytest
	pushd Files
	zip -r nsd.csar . -x ".*" -x "*/.*" -x "scripts/common/*"
	popd
	zip ../connectivitytest.csar Files/nsd.csar Definitions/experiment.yaml TOSCA-Metadata/TOSCA.meta TOSCA-Metadata/Metadata.yaml
	popd
	rm connectivitytest/Files/nsd.csar
}

function create_csar {
	PACKAGENAME=$1
	if [ ! -z $PACKAGENAME -a -d $PACKAGENAME -a -d ${PACKAGENAME}/Files ]; then
		pushd $PACKAGENAME
		pushd Files
		zip -r nsd.csar . -x ".*" -x "*/.*" -x "scripts/common/*"
		popd
		zip ../${PACKAGENAME}.csar Files/nsd.csar Definitions/experiment.yaml TOSCA-Metadata/TOSCA.meta TOSCA-Metadata/Metadata.yaml
		rm Files/nsd.csar
		popd
	fi
}

## this function will create links from the common scripipts folder to the machine tpe specifit folders
function create_links_nsd {
	pushd Files/scripts
	for d in adsvm ericssonvm fokusdevvm fokusvm surreyvm; do
		echo "## creating links for $d"
		for f in common/*; do
			FILENAME=$(basename $f)
			if [ "${FILENAME}" != "${d}_connect.sh" ]; then
				ln -f -s ../$f ${d}/${FILENAME}
			else
				echo "## skipping $FILENAME for $d"
			fi
		done
	done
	popd
}

function do_all_csar {
	for f in */Definitions/experiment.yaml; do
		DIRNAME=$(dirname $(dirname $f))
		if [ ! -z $DIRNAME ]; then
			echo "Processing $DIRNAME"
			create_csar $DIRNAME
		fi
	done
}

do_all_csar