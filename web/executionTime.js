import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

function formatExecutionTime(time) {
    return `${(time / 1000.0).toFixed(2)}s`;
}

function drawBadge(node, orig, restArgs) {
    let ctx = restArgs[0];
    const r = orig?.apply?.(node, restArgs);

    if (!node.flags.collapsed && node.constructor.title_mode != LiteGraph.NO_TITLE) {
        let text = "";
        let bgColor = "#ffa500"; // 正在执行时为橙色

        if (node.ty_et_start_time !== undefined) {
            const currentTime = performance.now();
            const elapsedTime = currentTime - node.ty_et_start_time;
            text = formatExecutionTime(elapsedTime);
        } else if (node.ty_et_execution_time !== undefined) {
            text = formatExecutionTime(node.ty_et_execution_time);
            bgColor = "#29b560"; // 执行完成后为绿色
        }

        if (!text) {
            return r;
        }

        ctx.save();
        ctx.font = "12px sans-serif";
        const textSize = ctx.measureText(text);
        ctx.fillStyle = bgColor;
        ctx.beginPath();
        const paddingHorizontal = 6;
        ctx.roundRect(0, -LiteGraph.NODE_TITLE_HEIGHT - 20, textSize.width + paddingHorizontal * 2, 20, 5);
        ctx.fill();

        ctx.fillStyle = "white";
        ctx.fillText(text, paddingHorizontal, -LiteGraph.NODE_TITLE_HEIGHT - paddingHorizontal);
        ctx.restore();
    }
    return r;
}

let updateInterval;

function startUpdateInterval() {
    if (!updateInterval) {
        updateInterval = setInterval(() => {
            app.graph.setDirtyCanvas(true, false);
        }, 100); // 每100毫秒更新一次
    }
}

function stopUpdateInterval() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
}

app.registerExtension({
    name: "TyDev-Utils.ExecutionTime",
    async setup() {
        app.ui.settings.addSetting({
            id: "TyDev.ExecutionTime.Enabled",
            name: "Show Execution Time",
            type: "boolean",
            defaultValue: true,
        });

        api.addEventListener("executing", ({ detail }) => {
            const nodeId = detail;
            if (!nodeId) {
                stopUpdateInterval();
                return;
            }
            const node = app.graph.getNodeById(nodeId);
            if (node) {
                node.ty_et_start_time = performance.now();
                node.ty_et_execution_time = undefined;
                startUpdateInterval();
            }
        });

        api.addEventListener("executed", () => {
            stopUpdateInterval();
        });

        api.addEventListener("TyDev-Utils.ExecutionTime.executed", ({ detail }) => {
            const node = app.graph.getNodeById(detail.node);
            if (node) {
                node.ty_et_execution_time = detail.execution_time;
                node.ty_et_start_time = undefined;
                app.graph.setDirtyCanvas(true, false);
            }
        });
    },
    async nodeCreated(node) {
        if (!node.ty_et_swizzled) {
            let orig = node.onDrawForeground;
            if (!orig) {
                orig = node.__proto__.onDrawForeground;
            }

            node.onDrawForeground = function (ctx) {
                if (app.ui.settings.getSettingValue("TyDev.ExecutionTime.Enabled", true)) {
                    drawBadge(node, orig, arguments);
                } else {
                    orig?.apply?.(node, arguments);
                }
            };
            node.ty_et_swizzled = true;
        }
    },
    async loadedGraphNode(node) {
        if (!node.ty_et_swizzled) {
            const orig = node.onDrawForeground;
            node.onDrawForeground = function (ctx) {
                if (app.ui.settings.getSettingValue("TyDev.ExecutionTime.Enabled", true)) {
                    drawBadge(node, orig, arguments);
                } else {
                    orig?.apply?.(node, arguments);
                }
            };
            node.ty_et_swizzled = true;
        }
    }
});