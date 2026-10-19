#!/bin/sh
# Limites reales i5-10500T (TDP 35W). Revertir: systemctl disable --now argos-powercap
for R in /sys/class/powercap/intel-rapl:0 /sys/class/powercap/intel-rapl-mmio:0; do [ -d $R ] || continue
echo 35000000 > $R/constraint_0_power_limit_uw
echo 50000000 > $R/constraint_1_power_limit_uw
done
echo "$(date -Is) PL1=35W PL2=50W" > /var/lib/argos/powercap-status
