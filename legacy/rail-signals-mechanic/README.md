# pak128.cs mechanical rail signals (backup)

These are the 15 `Mechanic_*` ČSD/DR semaphore objects (by Lubak91) from pak128.cs
`infrastructure.rail_signals.pak`, split into their own pak with their original names, data and
images: `infrastructure.rail_signals_mechanic.pak`. The rest of that pak is replaced by
`VZ-Signals-rail.pak` (see `signal-rail/`). The semaphores stay installed as they are and are not
part of the VZ set.

The only change: the three `Mechanic_CSD_LongSignal_*` objects now carry the long-block flag alone
(0x40) instead of 0x48, which is what today's makeobj writes for `is_longblocksignal=1`. The engine
only checks 0x40.

Rebuild (stock makeobj, from this folder):

```
python ../../tools/sign_extract.py <pak128.cs>/infrastructure.rail_signals.pak sprites --dat rail_signals_mechanic.dat --only Mechanic_...
makeobj pak128 infrastructure.rail_signals_mechanic.pak ./
```

Install: copy the `.pak` into the pakset folder, and remove `infrastructure.rail_signals.pak` in the
same step. Otherwise the 15 names are doubled.
