# alzo

This idea started from a voice-activated dashcam (https://www.youtube.com/watch?v=QeX0wYlnUt0). I then immediately thought about the dismal state of most Microsoft bloatware and reminisced about old, useful, if not at least fun, background daemons like Clippy or desktop pets. So I made alzo, a desktop assistant/pet that reacts to voice-commands!

## Recording & Rendering

An audio recording has to be captured for a given amount of time. You can't buffer into an audio device to then trigger an interrupt. The next question then is the "gather audio step" a blocking step though? - Doesn't seem like it because the rendering thread is still allowed to run whilst this is ocurring 

The second portion of this is the rendering the display. A display typically renders on a cycle, but how is this coordinated via an async mechanism. There is something besides threads which can let any windowing framework function right?

