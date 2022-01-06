#!/bin/bash

eval $(ssh-agent)
ssh-add $1

