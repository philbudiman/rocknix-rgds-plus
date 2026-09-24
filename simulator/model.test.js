const assert = require("node:assert/strict");
const { createState, dispatch, gamesFromNames } = require("./model.js");

const names = gamesFromNames(["/roms/Zeta.NDS", "Alpha.zip", "notes.txt", "Zeta.NDS"]);
assert.deepEqual(names, ["Alpha.zip", "Zeta.NDS"]);

let state = createState(names);
state = dispatch(state, { type: "move", step: -1 });
assert.equal(state.games[state.selected], "Zeta.NDS");
state = dispatch(state, { type: "launch" });
assert.equal(state.running, true);
assert.equal(dispatch(state, { type: "move", step: 1 }).selected, state.selected);
state = dispatch(state, { type: "exit" });
assert.equal(state.running, false);
assert.deepEqual(dispatch(createState([]), { type: "launch" }), createState([]));
