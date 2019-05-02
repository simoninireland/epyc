.. _concepts-parallel:

.. currentmodule:: epyc

Parallel processing concepts
----------------------------

If you've only ever used "normal" desktop software, then the idea of computing in parallel might be new to you.

Inside every computer there are a number of **cores** that do the actual work of running your programs.
Traditional machines have a single core. This might suggest that they can therefore only run a single
program at a time, and that's actually the case. This is referred to a **sequential execution**, meaing that
the jobs the computer does happen one at a time, in sequence.

But aren't you always using your computer to do multiple things at a time? -- checking your email while a movie
plays in the background, for example? What actually happens is that the single core in your machine switches between
programs very quickly, doing a little piece of one and then a little piece of the next, and so forth --- playing a couple
of frames of your movie in between your email keystrokes. This is still sequential execution, but giving the illusion
that more than one things happens at once. It's basically the same illusion that lets sixty still pictures played
one after the other each second give you the illusion of a continuous movie.

Given that you're not actually doing several things simultaneously under sequential execution, you might imagine that
each individual program runs slower: if two programs are sharing one core, then they only get half the attention that
they'd get if they had the core to themselves. This is essentially true (although it's a little bit more complicated
in practice). For human-centric computing it's often not much of an issue, but when we're considering scientific
computing where we want to get a lot of computation done, this is clearly going to be an issue. No matter how fast the
single core is, it's clear that doing 200 runs of a computation is going to take (at least) 200 times as long as doing
1 run.

In the past we relied on single cores getting faster and faster, according to something called
`Moore's law <https://en.wikipedia.org/wiki/Moore%27s_law>`_. There's obviously another way, however,
which is to use more than one core. This leads to **parallel execution**, where more than one thing *actually*
happens at one time rather than just *seeming* to happen -- even if the cores themselves are still doing
sequential execution.

There are a lot of ways to build a system capable of parallel execution, but the three most common ways these
days are:

1. build a **multicore** machine that has several cores -- 2, 8, 16, even 64 cores -- each of which can
   run a program;
2. take a set of single-core machines connected by a network, and run a program on each; or
3. do both of the above, a network of multicore machines.

The first option means buying a larger, multicore workstation; the second and third mean getting access to a
collection of machines for your programs. Cloud computing providers almost always use option three.

How fast can paralell execution make our program? We measure the increased performance using **speedup**, which is
the ratio of how long a task takes to complete in parallel compared to how long the *same* task would take under
sequential execution. You might think that, if an experiment takes 6400s on one machine, if you find 64 cores it
would take only 100s -- a speedup of 64. In fact things are more complicated than this, and you never get exactly
this *linear* speedup: but you can get very decent reductions in runtimes.

There's a problem still remaining, though. If a program has been written for sequential execution -- and the vast
majority of software is -- then it can't automatically make use of multiple cores. The code has to be **paralleelised**,
re-written to exploit parallelism, either by hand or by a clever compiler. Both these approaches have their own challenges.

However, there's one class of program that is trivially easy to parallelise, and that's a program that consists of
lots of *independent* executions of tasks. Tnis means that, instead of taking the pool of tasks and running them
one after another on a single core, we take the *same* tasks and divide them between the cores we have available.
This style of parallelisation is called a **task farm**, and it's exactly the class of program that ``epyc``
is designed to implement. Each experiment is still run sequentially, and so doesn't get any faster; but several
experiments, at diffewrent points in the parameter space, can be running simultaneously -- as many as we have
cores available. You can therefore think of ``epyc`` as a task farm generator for experiments, which handles all the
complexities of paralleising your still-seequential experimental code. It's important to realise that your
*individual experiment* is still run sequentially -- but the *collection* of experiments runs in parallel, and this
is where the speedup comes from.




