#!/bin/bash 
echo $1
rm $1.xcm
cat << EOF > xspec_model.tcl
#!/usr/bin/env xspec
set xs_return_result 1
query yes
model $1
/*

save model $1.xcm
log $1.par
show parameters
log none
exit
EOF

xspec - xspec_model.tcl

gawk '/^\ /' $1.xcm > $1.dat1
gawk '/^\#\ \ /' $1.par > $1.dat2
