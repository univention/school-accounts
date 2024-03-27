#!/bin/bash
# Copyright (C) 2024 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

APPCENTER_CACHE="/var/cache/univention-appcenter/appcenter-test.software-univention.de/5.0/"

install_apps_via_cmdline_no_update () {
	local username=${1:?missing username} password=${2:?missing password} rv=0 app password_file
	shift 2 || return $?
	password_file="$(mktemp)"
	echo "$password" > "$password_file"
	for app in "$@"; do
		univention-app install --noninteractive --username "$username" --pwdfile "$password_file" "$app" || rv=$?
	done
	rm -f "$password_file"
	return $rv
}

install_local_app_version () {
  local app_file_dir=$1
  local docker_image=$2
  shift 2
  sed -i "s/Version = .*/Version = 0.0.0-ci/" appcenter-management/ini
  if [ -n "$docker_image" ]; then
    echo "Using $docker_image for app install."
    sed -i "s#image: .*#image: $docker_image#" appcenter-management/compose
  else
    echo "Not changing docker image."
  fi
  for file in $(ls $app_file_dir); do
    cp "$app_file_dir/$file" "$APPCENTER_CACHE/ucsschool-user-management_00000000000000.$file"
  done
  env --chdir $APPCENTER_CACHE tar -rf .all.tar "$(ls ucsschool-user-management_00000000000000.*)"
  install_apps_via_cmdline_no_update Administrator univention ucsschool-user-management=0.0.0-ci
}
