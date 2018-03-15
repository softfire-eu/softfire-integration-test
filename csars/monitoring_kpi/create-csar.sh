#!/bin/bash

INNER_CSAR_FILE="custom_nsd.csar"
DELETE_INNER_CSAR=true

function create_csar {
	PACKAGENAME=$1
	if [ ! -z $PACKAGENAME -a -d $PACKAGENAME -a -d ${PACKAGENAME}/Files ]; then
		pushd $PACKAGENAME
		pushd Files
		zip -r $INNER_CSAR_FILE . -x ".*" -x "*/.*"
		popd
		zip ../"monitoring_"${PACKAGENAME}.csar Files/${INNER_CSAR_FILE} Definitions/experiment.yaml TOSCA-Metadata/TOSCA.meta TOSCA-Metadata/Metadata.yaml
		${DELETE_INNER_CSAR} && rm Files/${INNER_CSAR_FILE}
		popd
	fi
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
