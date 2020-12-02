Common problems with clusters
-----------------------------

``ipyparallel`` is a fairly basic cluster management system, but one that's adequate
for a lot of strightforward experiments. That means it sometimes need tweaking to
work effectively, in ways that rely on you (the user) rather than being automated
as might be the case in a more advanced system.

The most common problem is one of overloading. This can occur both for both
:ref:`multicore <multicore-parallel>` and :ref:`multi-machine <sharedfs-parallel>`
set-ups, and is when the machine spends so long doing your experiments that it 
stops being able to do other work. While this may sound like a good thing -- an efficient
use of resources -- some of that "other" work includes communicating with the
cluster controller. It's possible that too many engines crowd-out something
essential, which often manifests itself in one of two ways:

1. You can't log-in to the machine or run simple processes; or
2. You can't retrieve results.

The solution is actually quite straightforward: don't run as much work! This
can easily be done by, for example, always leaving one or two cores free on
each machine you use: so an eight-core machine would run six engines, leaving
two free for other things.
 

