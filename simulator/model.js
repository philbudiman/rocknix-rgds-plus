const SimulatorModel = (() => {
  const sampleGames = [
    "Sample Adventure.nds",
    "Sample Puzzle.zip",
    "Sample Racing.7z",
  ];

  function gamesFromNames(names) {
    return [...new Set(names
      .map((name) => name.split(/[\\/]/).pop())
      .filter((name) => /\.(nds|zip|7z)$/i.test(name)))]
      .sort((a, b) => a.localeCompare(b, undefined, { sensitivity: "base" }));
  }

  function createState(names = sampleGames) {
    return { games: gamesFromNames(names), selected: 0, running: false };
  }

  function dispatch(state, action) {
    if (action.type === "load") return createState(action.names);
    if (action.type === "exit") return { ...state, running: false };
    if (state.running || !state.games.length) return state;
    if (action.type === "launch") return { ...state, running: true };
    if (action.type === "select") {
      const selected = (action.index + state.games.length) % state.games.length;
      return { ...state, selected };
    }
    if (action.type === "move") {
      const selected = (state.selected + action.step + state.games.length) % state.games.length;
      return { ...state, selected };
    }
    return state;
  }

  return { sampleGames, gamesFromNames, createState, dispatch };
})();

if (typeof module !== "undefined") module.exports = SimulatorModel;
