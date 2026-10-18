import { describe, expect, it } from "vitest";
import { counterState } from "../src/components/Counter";

describe("counterState", () => {
  it("is ok below 90% of the limit", () => {
    expect(counterState(0, 10)).toBe("ok");
    expect(counterState(8, 10)).toBe("ok");
  });

  it("is near at or above 90% and not over", () => {
    expect(counterState(9, 10)).toBe("near");
    expect(counterState(10, 10)).toBe("near");
  });

  it("is over past the limit", () => {
    expect(counterState(11, 10)).toBe("over");
  });
});
