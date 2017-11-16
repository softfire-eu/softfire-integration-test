#!/bin/bash

INNER_CSAR_FILE="nsd.csar"


function create_csar {
	PACKAGENAME=$1
	if [ ! -z $PACKAGENAME -a -d $PACKAGENAME -a -d ${PACKAGENAME}/Files ]; then
		pushd $PACKAGENAME
		pushd Files
		zip -r $INNER_CSAR_FILE . -x ".*" -x "*/.*" -x "scripts/common/*"
		popd
		zip ../${PACKAGENAME}.csar Files/${INNER_CSAR_FILE} Definitions/experiment.yaml TOSCA-Metadata/TOSCA.meta TOSCA-Metadata/Metadata.yaml
		rm Files/${INNER_CSAR_FILE}
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