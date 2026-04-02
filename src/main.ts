import { Notice, Plugin, TFile } from "obsidian";
import { mdToHtml } from "./converter";
import { writeFileSync } from "fs";
import { join } from "path";
// @ts-ignore
import { shell } from "electron";

function getVaultBasePath(vault: any): string {
  return vault.adapter.basePath;
}

export default class Obs2FeishuPlugin extends Plugin {
  async onload() {
    // 注册文件菜单项（右键菜单 / 更多选项）
    this.registerEvent(
      this.app.workspace.on("file-menu", (menu, file) => {
        if (!(file instanceof TFile) || file.extension !== "md") return;

        menu.addItem((item) => {
          item
            .setTitle("导出为飞书 HTML")
            .setIcon("file-output")
            .onClick(async () => {
              await this.exportFile(file);
            });
        });
      })
    );

    // 注册命令面板命令
    this.addCommand({
      id: "export-current-file",
      name: "导出当前文件为飞书 HTML",
      checkCallback: (checking: boolean) => {
        const file = this.app.workspace.getActiveFile();
        if (!file || file.extension !== "md") return false;
        if (!checking) {
          this.exportFile(file);
        }
        return true;
      },
    });
  }

  async exportFile(file: TFile) {
    const notice = new Notice("正在转换...", 0);

    const logFn = (msg: string) => {
      console.log(`[obs2feishu] ${msg}`);
    };

    try {
      const html = await mdToHtml(file, this.app.vault, logFn);

      const basePath = getVaultBasePath(this.app.vault);
      const htmlRelPath = file.path.replace(/\.md$/, ".html");
      const absPath = join(basePath, htmlRelPath);
      writeFileSync(absPath, html, "utf-8");

      notice.hide();
      new Notice(`已导出: ${htmlRelPath}`, 8000);

      shell.openPath(absPath);
    } catch (err) {
      notice.hide();
      new Notice(`转换失败: ${err}`);
    }
  }
}
