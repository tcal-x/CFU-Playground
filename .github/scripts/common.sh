#!/bin/bash
#
# Copyright (C) 2020  The SymbiFlow Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

function tuttest_exec() {
  echo -e "\e[93mExecuting tuttest $@\e[39m"
  (echo "trap 'printf \"+ %s\\n\" \"\$BASH_COMMAND\" >&2' DEBUG"; tuttest "$@") | bash -e -
}
