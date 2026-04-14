#!/usr/bin/bash

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# This is an example for a script that activates the virtual environment and launches the app.
# Replace the project directory with the one you use.

project_directory="/foo/bar/BMA-Simulator"

cd  $project_directory || (echo "Starting bma_control failed: Unable to open specified project directory $project_directory"; exit)
source .venv/bin/activate
python ./bma_control
cd ~ || exit
