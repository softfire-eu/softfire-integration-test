#!/bin/bash

INNER_CSAR_FILE="nsd.csar"
DELETE_INNER_CSAR=true

function create_csar {
	PACKAGENAME=$1
	if [ ! -z $PACKAGENAME -a -d $PACKAGENAME ]; then
		pushd $PACKAGENAME
		if [ -d Files ]; then
		    pushd Files
		    zip -r $INNER_CSAR_FILE . -x ".*" -x "*/.*" -x "scripts/common/*"
		    popd
		    zip ../${PACKAGENAME}.csar Files/${INNER_CSAR_FILE} Definitions/experiment.yaml TOSCA-Metadata/TOSCA.meta TOSCA-Metadata/Metadata.yaml
		    ${DELETE_INNER_CSAR} && rm Files/${INNER_CSAR_FILE}
		else
		    zip ../${PACKAGENAME}.csar Definitions/experiment.yaml TOSCA-Metadata/TOSCA.meta TOSCA-Metadata/Metadata.yaml
		fi
		popd
	else
	  echo "------------------ $1"
	fi
}

## this function will create links from the common scripts folder to the machine tpe specific folders
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
