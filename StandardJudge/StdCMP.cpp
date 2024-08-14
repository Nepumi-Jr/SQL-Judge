/*
    -Stand Comparison-

    Use for just compare each item in output and solution file.

    Input by argument
    [1] is Solution path file
    [2] is input path file
    [3] is Source code path file
    output use name as "output.txt"

    output by File-stream named "grader_result.txt".

*/
#include<fstream>
#include<string>
using namespace std;

ifstream outFile;
ifstream solFile;
ofstream result;


int main(int argc, char const *argv[])
{
    outFile.open("output.txt");
    solFile.open(string(argv[1]));
    result.open("grader_result.txt");

    string outContent,solContent;
    

    while( outFile>>outContent && solFile>>solContent){
        if (outContent != solContent){
            result<<"W";

            outFile.close();
            solFile.close();
            return 0;
        }
    }

    if(outFile>>outContent || solFile>>solContent) {
        result<<"W";

        outFile.close();
        solFile.close();
        return 0;
    }

    result<<"P";

    outFile.close();
    solFile.close();
    return 0;
}




