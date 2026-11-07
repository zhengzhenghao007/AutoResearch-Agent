Upstream: https://github.com/junbolian/Academic-Humanizer
Revision: 62b0a02627e063015466c70f0a4dd4929a9f7f5b
License: LICENSE.txt (MIT)
Local adaptation: Doc accepts optional in-memory text so a report never needs a temporary manuscript file. The original file-based checker CLI remains available. services/academic_humanizer.py implements automatic Cleanup using the bundled lexicon and invariant extractor. It permits a narrower set of edits than interactive revision.
