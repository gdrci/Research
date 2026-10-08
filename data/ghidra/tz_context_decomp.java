// Ghidra decompile script used for data/secure/tz_context_creator_decomp.txt (Ghidra 12.1.3).
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
public class tz_context_decomp extends GhidraScript {
  public void run() throws Exception {
    AddressSpace s = currentProgram.getAddressFactory().getDefaultAddressSpace();
    DecompInterface di = new DecompInterface();
    di.openProgram(currentProgram);
    String[] addrs = args();
    for (String h : addrs) {
      Address a = s.getAddress(Long.parseLong(h,16));
      Function f = currentProgram.getFunctionManager().getFunctionContaining(a);
      if (f == null) { disassemble(a); createFunction(a, null); f = currentProgram.getFunctionManager().getFunctionAt(a); }
      if (f == null) { println("NO FUNCTION " + h); continue; }
      DecompileResults r = di.decompileFunction(f, 120, monitor);
      println("=== " + f.getName() + " @ " + f.getEntryPoint());
      if (r.getDecompiledFunction() != null) println(r.getDecompiledFunction().getC());
      else println("decompile failed: " + r.getErrorMessage());
    }
  }
  private String[] args() { return new String[]{"1c108320","1c0970dc","1c089f1c","1c07fa84"}; }
}
