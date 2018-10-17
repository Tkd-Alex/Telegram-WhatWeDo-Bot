#!/bin/sh

mkdir TreeTagger
cd TreeTagger
wget http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.1.tar.gz
wget http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tagger-scripts.tar.gz
wget http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/install-tagger.sh
wget http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/italian.par.gz

sh install-tagger.sh